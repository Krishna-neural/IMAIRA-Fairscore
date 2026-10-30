import re
from typing import Any, Dict, List

FILLERS = {"um", "uh", "like", "you know", "actually", "basically", "so"}

def score_communication(
    transcript_text: str,
    duration_seconds: float = 60.0,
    segments: List[Dict[str, Any]] = None
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

    # Restarts heuristic (repeated adjacent words, e.g. "we we", "I I")
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
