import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_PATH = BASE_DIR / "config.yaml"
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {"mock": True}

def enforce_word_limit(text: str, max_words: int = 30) -> str:
    words = text.strip().split()
    if len(words) <= max_words:
        return text.strip()
    truncated = " ".join(words[:max_words])
    if not truncated.endswith((".", "!", "?")):
        truncated = truncated.rstrip(",;:-") + "."
    return truncated

def _generate_with_gemini(criterion: str, marks_lost: float, quote: str, max_words: int = 30) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or "placeholder" in api_key.lower() or "your_" in api_key.lower():
        return f"Focus on {criterion} to avoid losing {marks_lost:.1f} marks by providing clear, accurate technical explanations."
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        prompt = (
            f"You are an expert interview evaluator. The candidate lost {marks_lost} marks in '{criterion}' "
            f"on quote: \"{quote}\". Provide exactly one actionable coaching fix sentence of at most {max_words} words."
        )
        response = client.models.generate_content(model=model, contents=prompt)
        raw_text = response.text.strip().replace("\n", " ") if response.text else ""
        return enforce_word_limit(raw_text, max_words=max_words)
    except Exception:
        return f"Address {criterion} specifically to recover lost marks by articulating core trade-offs clearly."

def generate_top_missed_feedback(
    candidates: List[Dict[str, Any]],
    top_n: int = 3,
    max_words: int = 30
) -> List[Dict[str, Any]]:
    sorted_candidates = sorted(
        candidates,
        key=lambda item: float(item.get("marks_lost", 0.0)),
        reverse=True
    )
    top_items = sorted_candidates[:top_n]
    result: List[Dict[str, Any]] = []

    for rank, item in enumerate(top_items, start=1):
        marks_lost = float(item.get("marks_lost", 0.0))
        criterion_id = str(item.get("criterion_id", f"crit_{rank}"))
        quote = str(item.get("quote", ""))
        fix = str(item.get("fix_sentence", ""))

        if not fix:
            cfg = load_config()
            if cfg.get("mock", True):
                fix = f"Improve response on {criterion_id} to avoid losing {marks_lost:.1f} marks during assessment."
            else:
                fix = _generate_with_gemini(criterion_id, marks_lost, quote, max_words)

        result.append({
            "point_id": rank,
            "criterion_id": criterion_id,
            "marks_lost": marks_lost,
            "timestamp_start": float(item.get("timestamp_start", 0.0)),
            "timestamp_end": float(item.get("timestamp_end", 0.0)),
            "quote": quote,
            "fix_sentence": enforce_word_limit(fix, max_words=max_words)
        })
    return result

def generate_feedback_from_criteria(
    criteria_scores: List[Dict[str, Any]],
    transcript: Optional[List[Dict[str, Any]]] = None,
    top_n: int = 3,
    max_words: int = 30
) -> List[Dict[str, Any]]:
    missed_candidates: List[Dict[str, Any]] = []
    default_transcript = transcript or []

    for idx, c in enumerate(criteria_scores):
        marks_lost = float(c.get("marks_lost", float(c.get("max_marks", 0.0)) - float(c.get("marks_awarded", 0.0))))
        if marks_lost <= 0.0:
            continue
        seg = default_transcript[idx % len(default_transcript)] if default_transcript else {}
        feedback_note = str(c.get("feedback", ""))
        fix = f"Refine {c.get('name', c.get('criterion_id'))}: {feedback_note}" if feedback_note else ""
        missed_candidates.append({
            "criterion_id": c.get("criterion_id", f"crit_{idx+1}"),
            "marks_lost": marks_lost,
            "timestamp_start": float(seg.get("start", 0.0)),
            "timestamp_end": float(seg.get("end", 0.0)),
            "quote": str(seg.get("text", "")),
            "fix_sentence": fix
        })

    return generate_top_missed_feedback(missed_candidates, top_n=top_n, max_words=max_words)

if __name__ == "__main__":
    sample_points = [
        {"criterion_id": "crit_1", "marks_lost": 4.0, "quote": "Index has no overhead", "fix_sentence": "Remember indexes trade disk write speed for faster read operations."},
        {"criterion_id": "crit_2", "marks_lost": 12.0, "quote": "We do not need transactions", "fix_sentence": "Explain ACID properties and emphasize how database transactions ensure consistency during concurrent updates and prevent data corruption in enterprise production systems."},
        {"criterion_id": "crit_3", "marks_lost": 8.0, "quote": "All queries run instantly", "fix_sentence": "Account for query complexity and execution plan bottlenecks."},
        {"criterion_id": "crit_4", "marks_lost": 2.0, "quote": "Use default settings", "fix_sentence": "Fine-tune buffer pools."}
    ]
    top_feedback = generate_top_missed_feedback(sample_points, top_n=3, max_words=30)
    for p in top_feedback:
        print(f"Rank {p['point_id']} | Criterion: {p['criterion_id']} | Lost: {p['marks_lost']} | Words: {len(p['fix_sentence'].split())} | Fix: {p['fix_sentence']}")
