import os
import sys
import re
import csv
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

# Ensure repo root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from rapidfuzz import fuzz, process
import jellyfish

from contracts.transcript import WordTiming, SuspiciousSpan

logger = logging.getLogger("imaira_asr.span_detector")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Common Indian-English / ASR acoustic confusions for interview technical terms
DEFAULT_ALIASES: Dict[str, str] = {
    "has map": "hash map",
    "hasmap": "hash map",
    "hashmap": "hash map",
    "link list": "linked list",
    "linklist": "linked list",
    "binary tree": "binary tree",
    "linklist": "linked list",
    "sinkronous": "synchronous",
    "asink": "async",
    "c plus plus": "C++",
    "c sharp": "C#",
    "dot net": ".NET",
    "postgress": "PostgreSQL",
    "postgre": "PostgreSQL",
    "no sequel": "NoSQL",
    "mongo": "MongoDB",
    "kubernets": "Kubernetes",
    "dockers": "Docker",
    "resursion": "recursion",
    "semfor": "semaphore",
    "semafor": "semaphore",
    "cubernetes": "Kubernetes",
    "reddis": "Redis",
    "asinc": "async",
    "polymorfism": "polymorphism",
    "im aira": "IMAIRA",
    "imaira": "IMAIRA",
    "fair score": "FairScore",
    "fairscore": "FairScore",
    "upta": "Gupta",
    "krishna upta": "Krishna Gupta",
    "bios variants trade of": "bias-variance tradeoff",
    "the bios variants trade of": "the bias-variance tradeoff",
    "bios variants": "bias-variance",
    "bios variant": "bias-variance",
    "bios": "bias",
    "biased": "bias",
    "and sensible methods": "ensemble methods",
    "sensible methods": "ensemble methods",
    "and sensible": "ensemble",
    "trade of": "tradeoff",
    "decates": "dictates",
    "servicing interest structure": "serving infrastructure",
    "interest structure": "infrastructure",
    "greatient decent": "gradient descent",
    "greatient": "gradient",
    "decent": "descent",
    "piper parameter": "hyperparameter",
    "iron value": "eigenvalue",
    "iron vector": "eigenvector",
    "wector": "vector",
    "over fitting": "overfitting",
    "under fitting": "underfitting",
}

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "from", "is", "was", "are", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "i", "you", "he", "she", "it",
    "we", "they", "my", "your", "his", "her", "its", "our", "their", "this",
    "that", "these", "those", "am"
}

def clean_text(text: str) -> str:
    """Normalize text by stripping punctuation and lowercasing."""
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()

class SuspiciousSpanDetector:
    """
    Detects suspicious spans in ASR transcripts using:
    1. Word confidence thresholding (identifies acoustically uncertain tokens).
    2. RapidFuzz fuzzy ratio matching against the technical glossary.
    3. Jellyfish phonetic similarity (Metaphone, Soundex) to catch accent shifts.
    4. Two-pass discrepancy analysis (comparing Pass A biased decode with Pass B).
    5. Custom alias dictionary matching.
    """

    def __init__(
        self,
        glossary: Optional[List[str]] = None,
        glossary_path: Optional[str] = "data/glossary.csv",
        confidence_threshold: float = 0.85,
        similarity_threshold: float = 75.0,
        phonetic_bonus: float = 12.0,
        custom_aliases: Optional[Dict[str, str]] = None
    ):
        self.conf_threshold = confidence_threshold
        self.sim_threshold = similarity_threshold
        self.phonetic_bonus = phonetic_bonus

        # Initialize aliases
        self.aliases = dict(DEFAULT_ALIASES)
        if custom_aliases:
            self.aliases.update(custom_aliases)

        # Load glossary
        self.terms: List[str] = []
        self.terms_lower: List[str] = []
        self._load_glossary(glossary, glossary_path)

        # Precompute phonetic keys for glossary terms
        self.metaphone_map: Dict[str, str] = {}
        self.soundex_map: Dict[str, str] = {}
        for term in self.terms:
            t_clean = clean_text(term)
            self.metaphone_map[term] = jellyfish.metaphone(t_clean)
            self.soundex_map[term] = jellyfish.soundex(t_clean)

        logger.info(
            f"SuspiciousSpanDetector initialized with {len(self.terms)} terms "
            f"(conf_thresh={self.conf_threshold}, sim_thresh={self.sim_threshold})"
        )

    def _load_glossary(self, glossary: Optional[List[str]], glossary_path: Optional[str]):
        if glossary:
            self.terms = [t.strip() for t in glossary if t.strip()]
        elif glossary_path:
            full_path = project_root / glossary_path
            if full_path.is_file():
                with open(full_path, "r", encoding="utf-8") as f:
                    if full_path.suffix.lower() == ".csv":
                        reader = csv.DictReader(f)
                        if "term" in reader.fieldnames:
                            self.terms = [row["term"].strip() for row in reader if row.get("term")]
                        else:
                            f.seek(0)
                            self.terms = [line.strip().split(",")[0] for line in f if line.strip()]
                    else:
                        self.terms = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for t in self.terms:
            if t.lower() not in seen:
                seen.add(t.lower())
                deduped.append(t)
        self.terms = deduped
        self.terms_lower = [t.lower() for t in self.terms]
        self.terms_set = set(self.terms_lower)

    def _is_known_term(self, word: str) -> bool:
        """Check if word or common inflection is already in technical glossary."""
        w = clean_text(word)
        if not w:
            return True
        if hasattr(self, 'terms_set') and w in self.terms_set:
            return True
        for suffix in ['s', 'es', 'ed', 'ing', 'ly', 'ize', 'ise', 'tion', 'able', 'ive']:
            if w.endswith(suffix):
                stem = w[:-len(suffix)]
                if hasattr(self, 'terms_set') and (stem in self.terms_set or (stem + 'e') in self.terms_set):
                    return True
        return False

    def _is_stop_span(self, words: List[WordTiming]) -> bool:
        """Return True if all words in span are stopwords or single non-alpha characters."""
        for w in words:
            clean = clean_text(w.word)
            if clean and clean not in STOPWORDS and len(clean) > 1:
                return False
        return True

    def score_candidate(self, span_text: str, target_term: str) -> Tuple[float, float, bool]:
        """
        Compute fuzzy lexical similarity and phonetic similarity.
        Returns: (fuzzy_score, combined_score, phonetic_match)
        """
        s_clean = clean_text(span_text)
        t_clean = clean_text(target_term)

        # 1. Lexical similarity
        fuzz_ratio = float(fuzz.ratio(s_clean, t_clean))
        token_sort = float(fuzz.token_sort_ratio(s_clean, t_clean))
        fuzzy_score = max(fuzz_ratio, token_sort)

        # 2. Phonetic matching
        span_meta = jellyfish.metaphone(s_clean)
        term_meta = self.metaphone_map.get(target_term, jellyfish.metaphone(t_clean))
        span_sdx = jellyfish.soundex(s_clean)
        term_sdx = self.soundex_map.get(target_term, jellyfish.soundex(t_clean))

        phonetic_match = False
        if span_meta and term_meta and span_meta == term_meta:
            phonetic_match = True
        elif span_sdx and term_sdx and span_sdx == term_sdx:
            phonetic_match = True

        # Combined score with phonetic boost
        combined_score = fuzzy_score
        if phonetic_match:
            combined_score += self.phonetic_bonus
        else:
            # Partial phonetic similarity credit
            meta_sim = fuzz.ratio(span_meta, term_meta)
            if meta_sim > 80.0:
                combined_score += (self.phonetic_bonus * 0.5)

        return fuzzy_score, min(combined_score, 100.0), phonetic_match

    def detect_spans(
        self,
        transcript: List[WordTiming],
        pass_a_transcript: Optional[List[WordTiming]] = None,
        candidate_terms: Optional[List[str]] = None,
        max_ngram: int = 4
    ) -> List[SuspiciousSpan]:
        """
        Inspect the transcript and return non-overlapping suspicious spans.
        """
        if not transcript:
            return []

        candidates: List[SuspiciousSpan] = []
        n_words = len(transcript)

        # 1. Cross-Pass Discrepancy Signal:
        # If Pass A produced a candidate term that differs from Pass B at the same timestamp range
        if pass_a_transcript and candidate_terms:
            a_text_full = " ".join(clean_text(w.word) for w in pass_a_transcript)
            for c_term in candidate_terms:
                c_clean = clean_text(c_term)
                if c_clean in a_text_full:
                    # Find time window of c_term in Pass A
                    a_words = [w for w in pass_a_transcript if clean_text(w.word) in c_clean.split()]
                    if a_words:
                        t_start = min(w.start for w in a_words) - 0.2
                        t_end = max(w.end for w in a_words) + 0.2

                        # Find corresponding words in Pass B (transcript)
                        matching_indices = [
                            i for i, w in enumerate(transcript)
                            if (w.end > t_start and w.start < t_end)
                        ]
                        if matching_indices:
                            start_i = matching_indices[0]
                            end_i = matching_indices[-1] + 1
                            span_slice = transcript[start_i:end_i]
                            span_text = " ".join(w.word.strip() for w in span_slice)
                            span_clean = clean_text(span_text)

                            # If text differs or confidence is low, register suspicion
                            if span_clean != c_clean:
                                confs = [w.conf for w in span_slice]
                                fuzz_sc, comb_sc, p_match = self.score_candidate(span_text, c_term)
                                candidates.append(SuspiciousSpan(
                                    span_id=f"span_{start_i}_{end_i}",
                                    start_idx=start_i,
                                    end_idx=end_i,
                                    t_start=span_slice[0].start,
                                    t_end=span_slice[-1].end,
                                    original_text=span_text,
                                    candidate_term=c_term,
                                    avg_conf=round(sum(confs) / len(confs), 4),
                                    min_conf=round(min(confs), 4),
                                    fuzzy_score=round(fuzz_sc, 1),
                                    phonetic_match=p_match,
                                    combined_score=max(round(comb_sc, 1), 85.0), # Strong signal from Pass A
                                    reason="pass_discrepancy"
                                ))

        # 2. Sliding n-gram evaluation across transcript (n = 1, 2, 3)
        for n in range(1, max_ngram + 1):
            for i in range(n_words - n + 1):
                span = transcript[i : i + n]
                confs = [w.conf for w in span]
                min_c = min(confs)
                avg_c = sum(confs) / len(confs)

                # Skip spans of pure stopwords or symbols
                if self._is_stop_span(span):
                    continue

                span_text = " ".join(w.word.strip() for w in span)
                span_clean = clean_text(span_text)

                # A. Direct alias dictionary match
                if span_clean in self.aliases:
                    target = self.aliases[span_clean]
                    if target.lower() == span_clean.lower():
                        continue
                    fuzz_sc, comb_sc, p_match = self.score_candidate(span_text, target)
                    candidates.append(SuspiciousSpan(
                        span_id=f"span_{i}_{i+n}",
                        start_idx=i,
                        end_idx=i + n,
                        t_start=span[0].start,
                        t_end=span[-1].end,
                        original_text=span_text,
                        candidate_term=target,
                        avg_conf=round(avg_c, 4),
                        min_conf=round(min_c, 4),
                        fuzzy_score=round(fuzz_sc, 1),
                        phonetic_match=p_match,
                        combined_score=95.0, # High confidence in alias match
                        reason="alias_match"
                    ))
                    continue

                # B. Low confidence trigger
                if min_c < self.conf_threshold:
                    if not self.terms or self._is_known_term(span_clean):
                        continue

                    # Search closest candidate in glossary via RapidFuzz
                    match = process.extractOne(span_clean, self.terms, scorer=fuzz.ratio)
                    if match:
                        best_term, best_score, _ = match
                        fuzz_sc, comb_sc, p_match = self.score_candidate(span_text, best_term)

                        # Check if criteria met (either high combined score OR moderate score with phonetic match)
                        if comb_sc >= self.sim_threshold or (fuzz_sc >= 70.0 and p_match):
                            candidates.append(SuspiciousSpan(
                                span_id=f"span_{i}_{i+n}",
                                start_idx=i,
                                end_idx=i + n,
                                t_start=span[0].start,
                                t_end=span[-1].end,
                                original_text=span_text,
                                candidate_term=best_term,
                                avg_conf=round(avg_c, 4),
                                min_conf=round(min_c, 4),
                                fuzzy_score=round(fuzz_sc, 1),
                                phonetic_match=p_match,
                                combined_score=round(comb_sc, 1),
                                reason="low_conf_glossary"
                            ))

        # 3. Greedy Non-Overlapping Selection
        # Sort candidates by combined_score descending, then prioritize longer spans
        candidates.sort(key=lambda s: (s.combined_score, s.end_idx - s.start_idx), reverse=True)

        selected: List[SuspiciousSpan] = []
        covered_indices = set()

        for cand in candidates:
            cand_indices = set(range(cand.start_idx, cand.end_idx))
            if not (cand_indices & covered_indices):
                selected.append(cand)
                covered_indices.update(cand_indices)

        # Sort selected spans chronologically
        selected.sort(key=lambda s: s.t_start)
        logger.info(f"Detected {len(selected)} suspicious spans in transcript.")
        return selected

def detect_suspicious_spans(
    transcript: List[WordTiming],
    pass_a_transcript: Optional[List[WordTiming]] = None,
    candidate_terms: Optional[List[str]] = None,
    glossary_path: str = "data/glossary.csv",
    confidence_threshold: float = 0.85
) -> List[SuspiciousSpan]:
    """Convenience functional wrapper for suspicious span detection."""
    detector = SuspiciousSpanDetector(
        glossary_path=glossary_path,
        confidence_threshold=confidence_threshold
    )
    return detector.detect_spans(
        transcript=transcript,
        pass_a_transcript=pass_a_transcript,
        candidate_terms=candidate_terms
    )
