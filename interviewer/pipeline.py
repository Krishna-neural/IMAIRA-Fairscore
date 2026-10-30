import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from interviewer.questions import RubricPoint

FILLERS = {"um", "uh", "like", "you know", "actually", "basically", "so"}

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

def score_communication(
    transcript_text: str,
    duration_seconds: float = 60.0,
    segments: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    duration_min = max(0.1, duration_seconds / 60.0)
    words = transcript_text.split()
    word_count = len(words)
    wpm = round(word_count / duration_min, 1)

    # 1. Pace score (ideal ~120 - 160 WPM)
    if 110 <= wpm <= 170:
        pace_score = 30.0
    elif 90 <= wpm < 110 or 170 < wpm <= 190:
        pace_score = 24.0
    else:
        pace_score = 18.0

    # 2. Filler word analysis
    lower_text = transcript_text.lower()
    filler_count = 0
    for f in FILLERS:
        filler_count += len(re.findall(r"\b" + re.escape(f) + r"\b", lower_text))
    filler_rate = round((filler_count / max(1, word_count)) * 100.0, 1)
    if filler_rate <= 3.0:
        filler_score = 25.0
    elif filler_rate <= 6.0:
        filler_score = 20.0
    else:
        filler_score = 14.0

    # 3. Pauses and restarts
    pause_count = 0
    if segments and len(segments) > 1:
        for i in range(len(segments) - 1):
            gap = float(segments[i+1].get("start", 0.0)) - float(segments[i].get("end", 0.0))
            if gap > 2.0:
                pause_count += 1
    pause_score = max(10.0, 25.0 - (pause_count * 3.0))

    restarts = len(re.findall(r"\b(\w+)\s+\1\b", lower_text))
    restart_score = max(10.0, 20.0 - (restarts * 3.0))

    total = min(100.0, round(pace_score + filler_score + pause_score + restart_score, 1))

    return {
        "score": int(total),
        "wpm": wpm,
        "filler_rate": filler_rate,
        "pause_count": pause_count,
        "restarts": restarts,
        "feedback": f"Speech rate: {wpm} WPM with {filler_count} fillers detected."
    }

def evaluate_content_and_structure(
    transcript_text: str,
    rubric_points: List[RubricPoint],
    question_text: str
) -> Dict[str, Any]:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = get_gemini_model()

    if api_key and not any(p in api_key.lower() for p in ["placeholder", "your_", "mock"]):
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are IMAIRA FairScore technical interviewer evaluating candidate response.\n"
                f"QUESTION: {question_text}\n"
                f"RUBRIC POINTS:\n" +
                "\n".join([f"- ID '{p.id}': {p.text}" for p in rubric_points]) +
                f"\n\nTRANSCRIPT:\n\"{transcript_text}\"\n\n"
                f"Output strictly JSON with format:\n"
                f"{{\n"
                f"  \"flags\": {{\"{rubric_points[0].id}\": \"covered\" | \"partial\" | \"missing\"}},\n"
                f"  \"structure_score\": int (1-100),\n"
                f"  \"issues\": {{\"{rubric_points[0].id}\": \"specific gap description\"}},\n"
                f"  \"evidence_spans\": {{\"{rubric_points[0].id}\": \"verbatim candidate quote\"}}\n"
                f"}}"
            )
            config = types.GenerateContentConfig(
                temperature=0.0,
                response_mime_type="application/json"
            )
            res = client.models.generate_content(model=model, contents=prompt, config=config)
            if res and res.text:
                parsed = json.loads(res.text.strip())
                flags = parsed.get("flags", {})
                struct_score = int(parsed.get("structure_score", 75))
                issues = parsed.get("issues", {})
                spans = parsed.get("evidence_spans", {})
                return {"flags": flags, "structure_score": struct_score, "issues": issues, "spans": spans}
        except Exception:
            pass

    # Deterministic heuristic fallback
    norm_t = transcript_text.lower()
    flags = {}
    issues = {}
    spans = {}
    for p in rubric_points:
        kw = [w for w in re.findall(r"\b[a-z]{4,}\b", p.text.lower()) if w not in {"which", "where", "other", "using", "their"}]
        matches = [w for w in kw if w in norm_t]
        ratio = len(matches) / len(kw) if kw else 0.0
        if ratio >= 0.40:
            flags[p.id] = "covered"
            spans[p.id] = " ".join([w for w in transcript_text.split() if w.lower() in matches][:10])
        elif ratio >= 0.20:
            flags[p.id] = "partial"
            issues[p.id] = f"Partially mentioned concepts related to {p.text}"
            spans[p.id] = " ".join([w for w in transcript_text.split() if w.lower() in matches][:8])
        else:
            flags[p.id] = "missing"
            issues[p.id] = f"Did not explain {p.text}"
            spans[p.id] = ""

    struct_score = 78 if len(norm_t.split()) >= 25 else 55
    return {"flags": flags, "structure_score": struct_score, "issues": issues, "spans": spans}

def run_fairscore_pipeline(
    transcript_text: str,
    word_tokens: Optional[List[Dict[str, Any]]] = None,
    rubric_points: Optional[List[Dict[str, Any]]] = None,
    question_text: str = "Explain indexing and concurrency in PostgreSQL.",
    duration_sec: float = 60.0
) -> Dict[str, Any]:
    # 1. Parse Rubrics
    r_objects = []
    if rubric_points:
        for p in rubric_points:
            r_objects.append(RubricPoint(
                id=str(p.get("id", p.get("criterion_id", "p1"))),
                text=str(p.get("text", p.get("name", ""))),
                weight=float(p.get("weight", p.get("max_marks", 1.0))),
                description=str(p.get("description", ""))
            ))
    else:
        r_objects = [
            RubricPoint("p1", "Explains index pointer structure and read acceleration", 1.0),
            RubricPoint("p2", "Details write amplification and maintenance penalty during DML", 1.0),
            RubricPoint("p3", "Explains multi-version concurrency control and locking mechanisms", 1.0)
        ]

    # 2. Content & Structure Scoring
    eval_data = evaluate_content_and_structure(transcript_text, r_objects, question_text)
    flags = eval_data["flags"]
    structure_score = eval_data["structure_score"]
    issues = eval_data.get("issues", {})
    spans = eval_data.get("spans", {})

    # Compute Content Score out of 100
    VAL = {"covered": 1.0, "partial": 0.5, "missing": 0.0}
    total_w = sum(p.weight for p in r_objects) or 1.0
    earned_w = sum(p.weight * VAL.get(flags.get(p.id, "missing"), 0.0) for p in r_objects)
    content_score = int(round((earned_w / total_w) * 100.0))

    # 3. Communication Scoring
    comm_res = score_communication(transcript_text, duration_seconds=duration_sec)
    comm_score = int(comm_res["score"])

    # 4. Top-3 Actionable Feedback
    feedback_items = []
    for p in r_objects:
        flag = flags.get(p.id, "missing")
        if flag in ("missing", "partial"):
            lost = 10 if flag == "missing" else 5
            quote = spans.get(p.id, "").strip()
            if not quote and transcript_text:
                quote = transcript_text[:min(100, len(transcript_text))]
            issue = issues.get(p.id, f"Incomplete coverage of {p.text}")
            fix = f"Explicitly explain {p.text} to secure full points."
            words = fix.split()
            if len(words) > 30:
                fix = " ".join(words[:30]) + "."
            feedback_items.append({
                "t_start": 18.2,
                "t_end": min(duration_sec, 27.0),
                "quote": quote,
                "issue": issue,
                "marks_lost": lost,
                "fix_sentence": fix
            })

    feedback_items.sort(key=lambda x: x["marks_lost"], reverse=True)
    top_feedback = feedback_items[:3]

    tokens = word_tokens or [
        {"word": w, "start": round(i * 0.4, 2), "end": round((i + 1) * 0.4, 2), "conf": 0.95, "corrected_from": None}
        for i, w in enumerate(transcript_text.split()[:20])
    ]

    return {
        "transcript": tokens,
        "scores": {
            "content": content_score,
            "structure": structure_score,
            "communication": comm_score
        },
        "flags": flags,
        "feedback": top_feedback
    }
