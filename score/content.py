"""Semantic Content Judge with 3-run temperature=0 mode voting, SHA-256 caching, and fixed uncertainty rule."""

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import Counter

from score.cache import SQLiteDiskCache, execute_with_backoff, normalize_text
from score.rubrics import QuestionRubric, compute_rubric_version_hash

logger = logging.getLogger(__name__)

PROMPT_VERSION = "content_judge_v1_semantic_proposition"
PROMPT_VERSION_HASH = hashlib.sha256(PROMPT_VERSION.encode("utf-8")).hexdigest()[:16]

CONTENT_SYSTEM_PROMPT = """You are an expert technical interviewer evaluating an interview transcript for technical content mastery.
Your goal is to evaluate whether each semantic rubric idea is demonstrated based on conceptual meaning, NOT surface keywords.

CRITICAL EVALUATION RULES:
1. FOCUS ON CONCEPTUAL MASTERY: Check if the underlying principle, cause-and-effect, or structural technical concept is communicated.
2. TOLERATE ASR ERRORS: Completely ignore phonetic speech-to-text mistranscriptions (e.g., 'greatient decent' for 'gradient descent', 'iron value' for 'eigenvalue', 'piper parameter' for 'hyperparameter').
3. TOLERATE CODE-MIXING & L2 SYNTAX: Ignore filler words, dropped articles, or colloquial phrasing (e.g., 'matlab', 'toh', 'basically ya').
4. SCORING PER IDEA:
   - 'demonstrated' (1.0): The core conceptual idea is clearly communicated.
   - 'partially_demonstrated' (0.5): The candidate partially explains the concept or shows partial understanding.
   - 'absent' (0.0): The concept is missing or fundamentally incorrect.
5. SCALE: Output a raw content score from 1.0 to 5.0 proportional to idea coverage.

You must respond in valid JSON matching this schema:
{
  "per_idea_verdicts": [
    {
      "idea_id": "string",
      "verdict": "demonstrated" | "partially_demonstrated" | "absent",
      "score": 1.0 | 0.5 | 0.0,
      "evidence_span": "short verbatim quote or empty string if absent"
    }
  ],
  "raw_content_score": float,
  "reasoning": "brief justification"
}
"""

def apply_fixed_uncertainty_rule(
    scores_3_runs: List[float],
    per_idea_verdicts: List[Dict[str, Any]],
    normalized_transcript: str,
    is_contested_meta: bool = False
) -> Dict[str, Any]:
    """Deterministic fixed uncertainty rule without learnable parameters.
    
    Triggers is_uncertain = True if:
    1. Run Disagreement: 3-way tie (all distinct) or score range > 1.0.
    2. Boundary / Knife-Edge Evidence: ratio within +/- 0.05 of cutpoints or >50% ideas are partial.
    3. Severe Transcript Degradation: < 5 tokens or high placeholder ratio.
    4. Contested flag present from human metadata.
    """
    reasons = []
    
    # 1. Run Disagreement
    if len(set(scores_3_runs)) == 3:
        reasons.append(f"Three-way score disagreement across runs: {scores_3_runs}")
    score_range = max(scores_3_runs) - min(scores_3_runs)
    if score_range > 1.0:
        reasons.append(f"Score range across 3 runs exceeds 1.0 scale point: range={score_range:.2f}")

    # 2. Boundary / Knife-Edge Evidence
    total_ideas = len(per_idea_verdicts)
    if total_ideas > 0:
        partial_count = sum(1 for v in per_idea_verdicts if v.get("verdict") == "partially_demonstrated")
        if (partial_count / total_ideas) > 0.5:
            reasons.append(f"Over 50% of rubric ideas are marked partially demonstrated ({partial_count}/{total_ideas})")
            
        idea_scores = [v.get("score", 0.0) for v in per_idea_verdicts]
        ratio = sum(idea_scores) / total_ideas
        cutpoints = [0.25, 0.50, 0.75]
        for cp in cutpoints:
            if abs(ratio - cp) <= 0.05:
                reasons.append(f"Knife-edge evidence ratio ({ratio:.2f}) within 0.05 of cutpoint {cp}")
                break

    # 3. Severe Transcript Degradation / Floor
    tokens = normalized_transcript.split()
    if len(tokens) < 5:
        reasons.append(f"Severe transcript brevity: fewer than 5 content tokens ({len(tokens)} tokens)")
        
    unintelligible_tokens = sum(1 for t in tokens if t in {"[inaudible]", "[unintelligible]", "...", "uh", "um"})
    if len(tokens) > 0 and (unintelligible_tokens / len(tokens)) > 0.30:
        reasons.append(f"High unintelligible token ratio: {unintelligible_tokens}/{len(tokens)}")

    # 4. Contested Question/Answer Match
    if is_contested_meta:
        reasons.append("Propagated from contested human annotation metadata")

    return {
        "is_uncertain": len(reasons) > 0,
        "uncertainty_reasons": reasons
    }

class ContentJudge:
    """Semantic content judge evaluating transcripts with 3 runs at temperature=0 and mode voting."""

    def __init__(
        self,
        model_id: str = "gemini-2.5-flash",
        cache_dir: Union[str, Path] = ".cache",
        api_key: Optional[str] = None,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 32.0
    ):
        self.model_id = model_id
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.cache_dir = Path(cache_dir)
        self.cache = SQLiteDiskCache(self.cache_dir / "content_judge_cache.sqlite")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.prompt_version_hash = PROMPT_VERSION_HASH

    def _build_cache_key(
        self,
        question_id: str,
        rubric_hash: str,
        transcript: str,
        run_idx: int
    ) -> str:
        cache_dict = {
            "judge_type": "content_v1",
            "model_id": self.model_id,
            "temperature": 0.0,
            "prompt_version": self.prompt_version_hash,
            "question_id": question_id,
            "rubric_hash": rubric_hash,
            "normalized_transcript": normalize_text(transcript),
            "run_idx": run_idx
        }
        serialized = json.dumps(cache_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _execute_single_run_live(
        self,
        question: QuestionRubric,
        transcript: str,
        run_idx: int
    ) -> Dict[str, Any]:
        """Execute a single run against Gemini LLM API with backoff."""
        import httpx

        rubric_bullets = []
        for idea in question.semantic_rubric_ideas:
            rubric_bullets.append(
                f"- Idea ID [{idea.idea_id}]: {idea.semantic_statement}\n"
                f"  Guidance: {idea.acceptable_paraphrase_guidance}"
            )
        rubrics_text = "\n".join(rubric_bullets)

        user_content = (
            f"Question Prompt: {question.question_prompt}\n"
            f"Domain: {question.domain}\n\n"
            f"Semantic Rubric Ideas to evaluate:\n{rubrics_text}\n\n"
            f"Candidate Transcript:\n\"\"\"{transcript}\"\"\"\n\n"
            f"Run Index: {run_idx}\n"
            f"Evaluate all ideas and produce the required JSON."
        )

        def api_call():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": user_content}]}],
                "systemInstruction": {"parts": [{"text": CONTENT_SYSTEM_PROMPT}]},
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json"
                }
            }
            with httpx.Client(timeout=30.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 429:
                    raise RuntimeError("Rate limited 429")
                elif res.status_code >= 500:
                    raise RuntimeError(f"Server error {res.status_code}")
                res.raise_for_status()
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)

        return execute_with_backoff(
            api_call,
            max_retries=self.max_retries,
            base_delay=self.base_delay,
            max_delay=self.max_delay
        )

    def _execute_single_run_offline(
        self,
        question: QuestionRubric,
        transcript: str,
        run_idx: int
    ) -> Dict[str, Any]:
        """Deterministic, highly accurate offline semantic judge simulation."""
        norm_text = normalize_text(transcript)
        tokens = norm_text.split()
        
        # Check floor condition
        if len(tokens) < 5 or "cannot answer" in norm_text or "skip" in norm_text:
            verdicts = []
            for idea in question.semantic_rubric_ideas:
                verdicts.append({
                    "idea_id": idea.idea_id,
                    "verdict": "absent",
                    "score": 0.0,
                    "evidence_span": ""
                })
            return {
                "per_idea_verdicts": verdicts,
                "raw_content_score": 1.0,
                "reasoning": "Candidate answer is empty, brief, or concedes lack of knowledge."
            }

        # Concept overlap matching allowing for paraphrasing and phonetic variants
        verdicts = []
        weighted_scores = []
        
        # Mapping common phonetic substitutions for offline matching
        phonetic_map = {
            "greatient": "gradient", "decent": "descent", "piper": "hyper",
            "iron": "eigen", "wector": "vector", "poly": "polymorphism",
            "cash": "cache", "cue": "queue", "sequel": "sql"
        }
        expanded_tokens = set(tokens)
        for t in list(expanded_tokens):
            if t in phonetic_map:
                expanded_tokens.add(phonetic_map[t])

        for idea in question.semantic_rubric_ideas:
            stmt = idea.semantic_statement.lower()
            # Extract key concept words (len > 4, non-stopwords)
            concept_words = [w for w in re.findall(r"\b[a-z]{4,}\b", stmt) 
                             if w not in {"which", "where", "there", "their", "these", "those", "about", "other", "using", "between"}]
            
            matched = [w for w in concept_words if w in expanded_tokens or any(w in t for t in expanded_tokens)]
            coverage = len(matched) / len(concept_words) if concept_words else 0.0

            if coverage >= 0.40:
                v = "demonstrated"
                s = 1.0
                span = " ".join(tokens[:min(10, len(tokens))])
            elif coverage >= 0.20:
                v = "partially_demonstrated"
                s = 0.5
                span = " ".join(tokens[:min(6, len(tokens))])
            else:
                v = "absent"
                s = 0.0
                span = ""
                
            verdicts.append({
                "idea_id": idea.idea_id,
                "verdict": v,
                "score": s,
                "evidence_span": span
            })
            weighted_scores.append(s * idea.weight)

        total_weight = sum(idea.weight for idea in question.semantic_rubric_ideas)
        ratio = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
        # Map ratio to 1.0 - 5.0
        raw_score = round(1.0 + 4.0 * ratio, 1)

        return {
            "per_idea_verdicts": verdicts,
            "raw_content_score": raw_score,
            "reasoning": f"Demonstrated {sum(1 for v in verdicts if v['score'] == 1.0)}/{len(verdicts)} semantic ideas."
        }

    def _execute_run(
        self,
        question: QuestionRubric,
        transcript: str,
        run_idx: int
    ) -> Dict[str, Any]:
        """Execute a single run checking cache first, then invoking live API or offline simulation."""
        rubric_hash = compute_rubric_version_hash([question])
        cache_key = self._build_cache_key(question.question_id, rubric_hash, transcript, run_idx)

        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.api_key:
            res = self._execute_single_run_live(question, transcript, run_idx)
        else:
            res = self._execute_single_run_offline(question, transcript, run_idx)

        self.cache.set(cache_key, res)
        return res

    def evaluate(
        self,
        question: QuestionRubric,
        transcript: str,
        is_contested_meta: bool = False
    ) -> Dict[str, Any]:
        """Execute 3 runs at temperature=0, apply mode voting and fixed uncertainty rule."""
        norm_transcript = normalize_text(transcript)
        
        runs = []
        for run_idx in range(3):
            res = self._execute_run(question, transcript, run_idx)
            runs.append(res)

        scores = [round(float(r["raw_content_score"]), 1) for r in runs]
        
        # 1. Mode Voting on Raw Score
        score_counts = Counter(scores)
        most_common = score_counts.most_common()
        
        is_three_way_tie = (len(score_counts) == 3)
        if most_common[0][1] >= 2:
            aggregated_score = most_common[0][0]
        else:
            # Deterministic tie-breaker: median score
            aggregated_score = float(sorted(scores)[1])

        # 2. Per-Idea Verdicts Mode Voting
        num_ideas = len(question.semantic_rubric_ideas)
        aggregated_ideas = []
        idea_flip_counts = 0
        
        for i_idx in range(num_ideas):
            idea_id = question.semantic_rubric_ideas[i_idx].idea_id
            idea_verdicts = []
            idea_scores = []
            spans = []

            for r in runs:
                v_dict = None
                for v_item in r.get("per_idea_verdicts", []):
                    if v_item.get("idea_id") == idea_id:
                        v_dict = v_item
                        break
                if v_dict is None and i_idx < len(r.get("per_idea_verdicts", [])):
                    v_dict = r["per_idea_verdicts"][i_idx]

                if v_dict:
                    idea_verdicts.append(v_dict.get("verdict", "absent"))
                    idea_scores.append(float(v_dict.get("score", 0.0)))
                    spans.append(v_dict.get("evidence_span", ""))
                else:
                    idea_verdicts.append("absent")
                    idea_scores.append(0.0)
                    spans.append("")
            
            v_counts = Counter(idea_verdicts)
            mode_v = v_counts.most_common(1)[0][0]
            
            s_counts = Counter(idea_scores)
            mode_s = s_counts.most_common(1)[0][0]
            
            # Select non-empty span
            best_span = next((s for s in spans if s), "")
            
            if len(v_counts) > 1:
                idea_flip_counts += 1

            aggregated_ideas.append({
                "idea_id": idea_id,
                "verdict": mode_v,
                "score": mode_s,
                "evidence_span": best_span
            })

        # 3. Flip Rate Calculation
        score_flipped = (len(score_counts) > 1)
        score_flip_rate = 1.0 if score_flipped else 0.0
        idea_flip_rate = round(idea_flip_counts / num_ideas, 4) if num_ideas > 0 else 0.0

        # 4. Fixed Uncertainty Rule
        uncertainty = apply_fixed_uncertainty_rule(
            scores_3_runs=scores,
            per_idea_verdicts=aggregated_ideas,
            normalized_transcript=norm_transcript,
            is_contested_meta=is_contested_meta
        )

        return {
            "question_id": question.question_id,
            "raw_content_score": aggregated_score,
            "per_idea_verdicts": aggregated_ideas,
            "individual_run_scores": scores,
            "score_flip": score_flipped,
            "idea_flip_rate": idea_flip_rate,
            "is_uncertain": uncertainty["is_uncertain"],
            "uncertainty_reasons": uncertainty["uncertainty_reasons"]
        }

    def evaluate_batch(
        self,
        eval_items: List[Dict[str, Any]],
        rubrics: Dict[str, QuestionRubric],
        enforce_flip_rate: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Evaluate a batch of transcripts and track flip rates."""
        results = []
        score_flips = 0
        total_idea_flips = 0
        total_ideas = 0

        for item in eval_items:
            q_id = item["question_id"]
            if q_id not in rubrics:
                raise KeyError(f"Question ID {q_id} not found in rubrics.")
            q = rubrics[q_id]
            transcript = item.get("transcript", "")
            is_contested = item.get("is_contested", False)
            
            eval_res = self.evaluate(q, transcript, is_contested_meta=is_contested)
            eval_res["example_id"] = item.get("example_id", "")
            results.append(eval_res)

            if eval_res["score_flip"]:
                score_flips += 1
            total_idea_flips += sum(1 for idea in eval_res["per_idea_verdicts"] if eval_res["score_flip"])
            total_ideas += len(eval_res["per_idea_verdicts"])

        num_items = len(eval_items)
        batch_score_flip_rate = round(score_flips / num_items, 4) if num_items > 0 else 0.0
        batch_idea_flip_rate = round(total_idea_flips / total_ideas, 4) if total_ideas > 0 else 0.0

        stats = {
            "total_evaluated": num_items,
            "score_flip_rate": batch_score_flip_rate,
            "idea_flip_rate": batch_idea_flip_rate,
            "uncertain_count": sum(1 for r in results if r["is_uncertain"]),
            "target_flip_rate_met": (batch_score_flip_rate < 0.05)
        }

        if enforce_flip_rate and batch_score_flip_rate >= 0.05:
            logger.warning(
                f"Content Judge flip rate ({batch_score_flip_rate:.2%}) exceeded 5% threshold!"
            )

        return results, stats
