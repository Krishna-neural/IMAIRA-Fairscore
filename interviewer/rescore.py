import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from interviewer.questions import get_question_by_id, get_rubric_points, RubricPoint

VAL: Dict[str, float] = {"covered": 1.0, "partial": 0.5, "missing": 0.0}

def get_gemini_model() -> str:
    """Retrieve active Gemini model dynamically from environment or project config.
    Guards against deprecated 'gemini-2.5-flash' which throws 404 NOT_FOUND.
    """
    model = os.environ.get("GEMINI_MODEL", "").strip()
    if not model or "2.5" in model:
        try:
            import yaml
            cfg_path = BASE_DIR / "config.yaml"
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    cfg_model = cfg.get("model", {}).get("name", "").strip()
                    if cfg_model and "2.5" not in cfg_model:
                        model = cfg_model
        except Exception:
            pass
    if not model or "2.5" in model:
        model = "gemini-3.5-flash"
    return model

def call_gemini(prompt: str, cache_key: Optional[str] = None, temperature: float = 0.0) -> Optional[str]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or any(p in api_key.lower() for p in ["placeholder", "your_", "mock"]):
        return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        model = get_gemini_model()
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json"
        )
        res = client.models.generate_content(model=model, contents=prompt, config=config)
        if res and res.text:
            return res.text.strip()
    except Exception:
        pass
    return None

def judge_targeted_reanswer(
    reanswer_text: str,
    point_id: str,
    point_text: str
) -> Dict[str, Any]:
    prompt = (
        f"You are evaluating a candidate's re-answer for a specific missed rubric point in an interview.\n"
        f"RUBRIC POINT ({point_id}): {point_text}\n"
        f"CANDIDATE RE-ANSWER:\n\"{reanswer_text}\"\n\n"
        f"Determine whether this re-answer now covers the concept.\n"
        f"Return ONLY a JSON object: {{\"flag\": \"covered\" | \"partial\" | \"missing\", \"reason\": str, \"confidence\": float}}"
    )

    cache_key = f"rescore:{point_id}:{reanswer_text}"
    raw = call_gemini(prompt, cache_key=cache_key, temperature=0.0)
    if raw:
        try:
            data = json.loads(raw)
            flag = data.get("flag", "partial").lower()
            if flag in VAL:
                return {
                    "flag": flag,
                    "reason": data.get("reason", "Evaluated via Gemini."),
                    "confidence": float(data.get("confidence", 0.95))
                }
        except Exception:
            pass

    # Deterministic fallback
    words = reanswer_text.lower().split()
    keywords = [w.lower() for w in point_text.split() if len(w) > 4]
    matches = sum(1 for k in keywords if k in words)
    if matches >= 2 or len(words) >= 15:
        flag = "covered"
    elif matches >= 1 or len(words) >= 8:
        flag = "partial"
    else:
        flag = "missing"

    return {
        "flag": flag,
        "reason": f"Targeted heuristic match on {matches} keywords.",
        "confidence": 0.85
    }

def rescore_segment(
    original_evaluation: Dict[str, Any],
    target_point_id: str,
    reanswer_text: str,
    question_id: str = "q_db_01"
) -> Dict[str, Any]:
    rubric_points = get_rubric_points(question_id)
    if not rubric_points:
        rubric_points = [
            RubricPoint("p1", "Explains indexing speedup", 1.0),
            RubricPoint("p2", "Details write overhead during DML", 1.0),
            RubricPoint("p3", "Explains concurrency and locks", 1.0)
        ]

    target_rp = next((p for p in rubric_points if p.id == target_point_id), None)
    if not target_rp:
        raise ValueError(f"Target rubric point '{target_point_id}' not found.")

    # 1. Judge the re-answer
    reanswer_result = judge_targeted_reanswer(reanswer_text, target_rp.id, target_rp.text)
    new_flag = reanswer_result["flag"]

    # 2. Compute delta
    old_flags = dict(original_evaluation.get("flags", {}))
    old_flag = old_flags.get(target_point_id, "missing")

    # Update flag map
    updated_flags = dict(old_flags)
    updated_flags[target_point_id] = new_flag

    # 3. Recalculate content score
    total_weight = sum(p.weight for p in rubric_points) or 1.0
    old_weighted = sum(p.weight * VAL.get(old_flags.get(p.id, "missing"), 0.0) for p in rubric_points)
    new_weighted = sum(p.weight * VAL.get(updated_flags.get(p.id, "missing"), 0.0) for p in rubric_points)

    old_content_score = int(round((old_weighted / total_weight) * 100.0))
    new_content_score = int(round((new_weighted / total_weight) * 100.0))
    score_gain = new_content_score - old_content_score

    # 4. Update overall scores object
    updated_scores = dict(original_evaluation.get("scores", {}))
    updated_scores["content"] = new_content_score

    # 5. Update feedback list
    old_feedback = list(original_evaluation.get("feedback", []))
    updated_feedback = []
    for item in old_feedback:
        if target_point_id in item.get("issue", "") or target_point_id in item.get("fix_sentence", "") or item.get("marks_lost", 0) > 0:
            if new_flag == "covered":
                continue
            elif new_flag == "partial":
                item["marks_lost"] = max(1, item.get("marks_lost", 10) // 2)
                item["issue"] = f"Partially improved: {reanswer_result['reason']}"
        updated_feedback.append(item)

    return {
        "target_point_id": target_point_id,
        "reanswer_text": reanswer_text,
        "before": {
            "flag": old_flag,
            "content_score": old_content_score,
            "scores": original_evaluation.get("scores", {})
        },
        "after": {
            "flag": new_flag,
            "content_score": new_content_score,
            "scores": updated_scores
        },
        "score_gain": score_gain,
        "resolved": new_flag == "covered",
        "reason": reanswer_result["reason"],
        "confidence": reanswer_result["confidence"],
        "updated_scores": updated_scores,
        "updated_flags": updated_flags,
        "updated_feedback": updated_feedback
    }
