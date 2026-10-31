import re
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz

def normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text).lower().strip()

def find_overlapping_segments(
    start: float,
    end: float,
    transcript: List[Dict[str, Any]],
    tolerance_sec: float = 2.0
) -> List[Dict[str, Any]]:
    overlapping = []
    for seg in transcript:
        s_start = float(seg.get("start", 0.0))
        s_end = float(seg.get("end", 0.0))
        if max(start - tolerance_sec, s_start) <= min(end + tolerance_sec, s_end):
            overlapping.append(seg)
    return overlapping

def validate_feedback_item(
    item: Dict[str, Any],
    transcript: List[Dict[str, Any]],
    tolerance_sec: float = 2.0,
    fuzzy_threshold: float = 80.0
) -> bool:
    t_start = float(item.get("timestamp_start", -1.0))
    t_end = float(item.get("timestamp_end", -1.0))
    quote = str(item.get("quote", "")).strip()

    if t_start < 0 or t_end < 0 or t_start > t_end or not quote or not transcript:
        return False

    overlapping = find_overlapping_segments(t_start, t_end, transcript, tolerance_sec)
    if not overlapping:
        return False

    combined_text = " ".join(str(seg.get("text", "")) for seg in overlapping)
    norm_quote = normalize_text(quote)
    norm_combined = normalize_text(combined_text)

    if norm_quote in norm_combined:
        return True

    score = fuzz.partial_ratio(norm_quote, norm_combined)
    return score >= fuzzy_threshold

def regenerate_feedback_item(
    item: Dict[str, Any],
    transcript: List[Dict[str, Any]],
    fuzzy_threshold: float = 75.0
) -> Optional[Dict[str, Any]]:
    quote = str(item.get("quote", "")).strip()
    if not quote or not transcript:
        return None

    norm_quote = normalize_text(quote)
    best_match: Optional[Tuple[float, Dict[str, Any]]] = None

    for seg in transcript:
        norm_seg = normalize_text(str(seg.get("text", "")))
        score = fuzz.partial_ratio(norm_quote, norm_seg)
        if score >= fuzzy_threshold:
            if best_match is None or score > best_match[0]:
                best_match = (score, seg)

    if not best_match:
        return None

    matched_seg = best_match[1]
    regenerated = dict(item)
    regenerated["timestamp_start"] = float(matched_seg.get("start", 0.0))
    regenerated["timestamp_end"] = float(matched_seg.get("end", 0.0))
    # If quote was severely altered, ground it to actual transcript fragment
    if norm_quote not in normalize_text(str(matched_seg.get("text", ""))):
        regenerated["quote"] = str(matched_seg.get("text", quote))
    return regenerated

def validate_and_filter_feedback(
    feedback_items: List[Dict[str, Any]],
    transcript: List[Dict[str, Any]],
    tolerance_sec: float = 2.0,
    fuzzy_threshold: float = 80.0
) -> List[Dict[str, Any]]:
    valid_items: List[Dict[str, Any]] = []

    for item in feedback_items:
        if validate_feedback_item(item, transcript, tolerance_sec, fuzzy_threshold):
            valid_items.append(dict(item))
            continue

        regenerated = regenerate_feedback_item(item, transcript, fuzzy_threshold=70.0)
        if regenerated and validate_feedback_item(regenerated, transcript, tolerance_sec, fuzzy_threshold=70.0):
            valid_items.append(regenerated)

    # Re-index survivor point_ids sequentially
    for idx, item in enumerate(valid_items, start=1):
        item["point_id"] = idx

    return valid_items

if __name__ == "__main__":
    test_transcript = [
        {"start": 10.0, "end": 20.0, "text": "PostgreSQL handles concurrency using multi-version concurrency control."},
        {"start": 21.0, "end": 35.0, "text": "Indexes can slow down write heavy workloads significantly."}
    ]
    test_items = [
        {"point_id": 1, "marks_lost": 6.0, "timestamp_start": 21.0, "timestamp_end": 35.0, "quote": "Indexes can slow down write heavy workloads", "fix_sentence": "Clarify indexing trade-offs."},
        {"point_id": 2, "marks_lost": 5.0, "timestamp_start": 99.0, "timestamp_end": 120.0, "quote": "PostgreSQL handles concurrency", "fix_sentence": "Explain MVCC mechanisms."},
        {"point_id": 3, "marks_lost": 4.0, "timestamp_start": 10.0, "timestamp_end": 20.0, "quote": "We use quantum computers for sorting.", "fix_sentence": "Nonsense point."}
    ]
    filtered = validate_and_filter_feedback(test_items, test_transcript)
    print(f"Original: {len(test_items)} items -> Filtered: {len(filtered)} items")
    for it in filtered:
        print(f"Point {it['point_id']} | Timestamps: {it['timestamp_start']}-{it['timestamp_end']} | Quote: {it['quote']}")
