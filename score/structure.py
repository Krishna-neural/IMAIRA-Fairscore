"""Independent Structural Organization and Argument Coherence Judge."""

import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections import Counter

from score.cache import SQLiteDiskCache, execute_with_backoff, normalize_text

logger = logging.getLogger(__name__)

STRUCTURE_PROMPT_VERSION = "structure_judge_v1_decoupled_bias_neutral"
STRUCTURE_PROMPT_VERSION_HASH = hashlib.sha256(STRUCTURE_PROMPT_VERSION.encode("utf-8")).hexdigest()[:16]

STRUCTURE_SYSTEM_PROMPT = """You are an expert communication and speech structure evaluator.
Your sole mission is to evaluate the candidate's structural communication organization, clarity, and argument flow.

EVALUATION CRITERIA (ONLY THESE THREE):
1. Framing / Directness (weight: 35%): Does the candidate address the core premise directly at the outset without rambling?
2. Logical Progression & Coherence (weight: 40%): Are ideas, causal steps, or tradeoffs presented in a clear, logical sequence?
3. Completeness of Closure / Summary (weight: 25%): Does the response reach a coherent, definitive conclusion or takeaway?

STRICT BIAS NEUTRALIZATION MANDATE:
- DO NOT penalize technical inaccuracies or incorrect factual statements (content is evaluated independently).
- DO NOT penalize non-native grammar, dropped articles, L2 syntax, or code-mixed discourse markers (e.g., 'matlab', 'toh', 'basically ya', 'like you know').
- DO NOT penalize phonetic ASR speech-to-text mistranscriptions (e.g., 'greatient decent', 'piper parameter').

Output must be strictly valid JSON matching this schema:
{
  "framing": {
    "score": float (1.0 to 5.0),
    "feedback": "string",
    "evidence_span": "verbatim text quote"
  },
  "coherence": {
    "score": float (1.0 to 5.0),
    "feedback": "string",
    "evidence_span": "verbatim text quote"
  },
  "closure": {
    "score": float (1.0 to 5.0),
    "feedback": "string",
    "evidence_span": "verbatim text quote"
  },
  "raw_structure_score": float (1.0 to 5.0),
  "reasoning": "brief justification"
}
"""

def apply_structure_uncertainty_rule(
    scores_3_runs: List[float],
    sub_scores: Dict[str, float],
    normalized_transcript: str
) -> Dict[str, Any]:
    """Fixed uncertainty rule for structure evaluations."""
    reasons = []
    
    # 1. Run Disagreement
    if len(set(scores_3_runs)) == 3:
        reasons.append(f"Three-way structure score disagreement across runs: {scores_3_runs}")
    score_range = max(scores_3_runs) - min(scores_3_runs)
    if score_range > 1.0:
        reasons.append(f"Structure score range across 3 runs exceeds 1.0 scale point: range={score_range:.2f}")

    # 2. Extreme Sub-Component Discordance
    vals = list(sub_scores.values())
    if vals and (max(vals) - min(vals)) >= 3.0:
        reasons.append(f"Extreme discordance between structure subcomponents: {sub_scores}")

    # 3. Severe Transcript Brevity / Floor
    tokens = normalized_transcript.split()
    if len(tokens) < 5:
        reasons.append(f"Severe transcript brevity: fewer than 5 tokens ({len(tokens)})")

    return {
        "is_uncertain": len(reasons) > 0,
        "uncertainty_reasons": reasons
    }

class StructureJudge:
    """Evaluates structural organization and coherence decoupled from technical correctness and ASR noise."""

    def __init__(
        self,
        model_id: str = "gemini-1.5-flash",
        cache_dir: Union[str, Path] = ".cache",
        api_key: Optional[str] = None,
        max_retries: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 32.0
    ):
        self.model_id = os.getenv("GEMINI_MODEL", model_id)
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.cache_dir = Path(cache_dir)
        self.cache = SQLiteDiskCache(self.cache_dir / "structure_judge_cache.sqlite")
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.prompt_version_hash = STRUCTURE_PROMPT_VERSION_HASH
        self._live_available = True

    def _build_cache_key(
        self,
        question_id: str,
        transcript: str,
        run_idx: int
    ) -> str:
        cache_dict = {
            "judge_type": "structure_v1",
            "model_id": self.model_id,
            "temperature": 0.0,
            "prompt_version": self.prompt_version_hash,
            "question_id": question_id,
            "normalized_transcript": normalize_text(transcript),
            "run_idx": run_idx
        }
        serialized = json.dumps(cache_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _execute_single_run_live(
        self,
        question_id: str,
        question_prompt: str,
        transcript: str,
        run_idx: int
    ) -> Dict[str, Any]:
        """Execute a single run against Gemini LLM API."""
        import httpx

        user_content = (
            f"Question Prompt: {question_prompt}\n\n"
            f"Candidate Transcript:\n\"\"\"{transcript}\"\"\"\n\n"
            f"Run Index: {run_idx}\n"
            f"Evaluate the structural communication quality according to the 3 criteria."
        )

        def api_call():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_id}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{"parts": [{"text": user_content}]}],
                "systemInstruction": {"parts": [{"text": STRUCTURE_SYSTEM_PROMPT}]},
                "generationConfig": {
                    "temperature": 0.0,
                    "responseMimeType": "application/json"
                }
            }
            with httpx.Client(timeout=2.0) as client:
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
        question_prompt: str,
        transcript: str,
        run_idx: int
    ) -> Dict[str, Any]:
        """Deterministic offline structural simulation invariant to ASR and code-mixing."""
        norm_text = normalize_text(transcript)
        words = norm_text.split()

        # Check floor
        if len(words) < 5 or "cannot answer" in norm_text or "skip" in norm_text:
            return {
                "framing": {"score": 1.0, "feedback": "No framing provided.", "evidence_span": ""},
                "coherence": {"score": 1.0, "feedback": "No argument progression.", "evidence_span": ""},
                "closure": {"score": 1.0, "feedback": "No closure.", "evidence_span": ""},
                "raw_structure_score": 1.0,
                "reasoning": "Transcript is insufficient to demonstrate structure."
            }

        # 1. Framing: Check direct engagement in first 15 words
        first_chunk = " ".join(words[:15])
        framing_score = 3.0
        if any(w in first_chunk for w in ["address", "speaking", "principle", "core", "looking", "in", "to"]):
            framing_score = 4.5
        elif any(w in first_chunk for w in ["uh", "sorry", "cannot", "remember", "not"]):
            framing_score = 2.0

        # 2. Coherence: Transition signals and multi-step progression
        transition_markers = ["furthermore", "also", "in addition", "moreover", "second", "while", "overall", "because", "therefore"]
        has_transitions = sum(1 for m in transition_markers if m in norm_text)
        if has_transitions >= 2 and len(words) >= 20:
            coherence_score = 4.5
        elif has_transitions >= 1 and len(words) >= 12:
            coherence_score = 3.5
        elif len(words) >= 8:
            coherence_score = 2.5
        else:
            coherence_score = 2.0

        # 3. Closure: Summary or practical takeaway
        closure_markers = ["optimal", "balance", "production", "real world", "conclude", "standard", "achieved", "overall"]
        has_closure = any(m in norm_text for m in closure_markers)
        if has_closure:
            closure_score = 4.5
        elif len(words) >= 15:
            closure_score = 3.0
        else:
            closure_score = 2.0

        # Weighted raw structure score: 0.35 framing + 0.40 coherence + 0.25 closure
        composite = round(0.35 * framing_score + 0.40 * coherence_score + 0.25 * closure_score, 1)
        composite = max(1.0, min(5.0, composite))

        return {
            "framing": {"score": framing_score, "feedback": "Directness in opening.", "evidence_span": first_chunk},
            "coherence": {"score": coherence_score, "feedback": f"Detected {has_transitions} transitions.", "evidence_span": " ".join(words[5:15]) if len(words) > 15 else ""},
            "closure": {"score": closure_score, "feedback": "Conclusion reached." if has_closure else "Partial closure.", "evidence_span": " ".join(words[-10:])},
            "raw_structure_score": composite,
            "reasoning": f"Structure composite {composite} from framing={framing_score}, coherence={coherence_score}, closure={closure_score}."
        }

    def _execute_run(
        self,
        question_id: str,
        question_prompt: str,
        transcript: str,
        run_idx: int
    ) -> Dict[str, Any]:
        cache_key = self._build_cache_key(question_id, transcript, run_idx)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        if self.api_key and getattr(self, "_live_available", True):
            try:
                res = self._execute_single_run_live(question_id, question_prompt, transcript, run_idx)
            except Exception as e:
                logger.warning(f"Live Gemini API call failed ({e}); falling back to deterministic offline structure judge.")
                self._live_available = False
                res = self._execute_single_run_offline(question_prompt, transcript, run_idx)
        else:
            res = self._execute_single_run_offline(question_prompt, transcript, run_idx)

        self.cache.set(cache_key, res)
        return res

    def evaluate(
        self,
        question_id: str,
        question_prompt: str,
        transcript: str
    ) -> Dict[str, Any]:
        """Execute 3 runs at temperature=0, apply mode voting and return structure result."""
        norm_transcript = normalize_text(transcript)

        runs = []
        for run_idx in range(3):
            r = self._execute_run(question_id, question_prompt, transcript, run_idx)
            runs.append(r)

        scores = [round(float(r["raw_structure_score"]), 1) for r in runs]
        score_counts = Counter(scores)
        most_common = score_counts.most_common()

        if most_common[0][1] >= 2:
            aggregated_score = most_common[0][0]
        else:
            # Deterministic median tie-breaker
            aggregated_score = float(sorted(scores)[1])

        # Subcomponent modes
        components = {}
        for comp in ["framing", "coherence", "closure"]:
            c_scores = [round(float(r[comp]["score"]), 1) for r in runs]
            c_counts = Counter(c_scores)
            c_mode = c_counts.most_common(1)[0][0]
            # Take first non-empty span
            spans = [r[comp].get("evidence_span", "") for r in runs]
            chosen_span = next((s for s in spans if s), "")
            feedbacks = [r[comp].get("feedback", "") for r in runs]
            chosen_fb = next((f for f in feedbacks if f), "")
            components[comp] = {
                "score": c_mode,
                "feedback": chosen_fb,
                "evidence_span": chosen_span
            }

        score_flipped = (len(score_counts) > 1)
        sub_score_dict = {k: v["score"] for k, v in components.items()}

        uncertainty = apply_structure_uncertainty_rule(
            scores_3_runs=scores,
            sub_scores=sub_score_dict,
            normalized_transcript=norm_transcript
        )

        return {
            "question_id": question_id,
            "raw_structure_score": aggregated_score,
            "components": components,
            "individual_run_scores": scores,
            "score_flip": score_flipped,
            "is_uncertain": uncertainty["is_uncertain"],
            "uncertainty_reasons": uncertainty["uncertainty_reasons"]
        }

    def evaluate_batch(
        self,
        eval_items: List[Dict[str, Any]],
        rubrics: Dict[str, Any],
        enforce_flip_rate: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        results = []
        flips = 0

        for item in eval_items:
            q_id = item["question_id"]
            prompt = rubrics[q_id].question_prompt if q_id in rubrics else item.get("question_prompt", "")
            transcript = item.get("transcript", "")
            
            res = self.evaluate(q_id, prompt, transcript)
            res["example_id"] = item.get("example_id", "")
            results.append(res)
            if res["score_flip"]:
                flips += 1

        n = len(eval_items)
        flip_rate = round(flips / n, 4) if n > 0 else 0.0

        stats = {
            "total_evaluated": n,
            "flip_rate": flip_rate,
            "uncertain_count": sum(1 for r in results if r["is_uncertain"]),
            "target_flip_rate_met": (flip_rate < 0.05)
        }

        if enforce_flip_rate and flip_rate >= 0.05:
            logger.warning(f"Structure Judge flip rate ({flip_rate:.2%}) exceeded 5% threshold!")

        return results, stats
