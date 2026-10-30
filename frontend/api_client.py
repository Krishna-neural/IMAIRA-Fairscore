"""Backend API client for the IMAIRA-Fairscore AI Mock Interviewer Frontend.

Handles communication with the FastAPI FairScore service and ASR worker,
with automatic graceful fallback to the local scoring pipeline when microservices
are not running as separate processes.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from score.pipeline import run_fairscore_pipeline

logger = logging.getLogger(__name__)

FAIRSCORE_URL = os.getenv("FAIRSCORE_URL", "http://localhost:8002").rstrip("/")
ASR_URL = os.getenv("ASR_URL", "http://localhost:8001").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("API_TIMEOUT", "15.0"))


def check_fairscore_health() -> Dict[str, Any]:
    """Check if the FairScore backend service is alive."""
    try:
        resp = requests.get(f"{FAIRSCORE_URL}/health", timeout=2.0)
        if resp.status_code == 200:
            data = resp.json()
            return {"online": True, "service": "fairscore", "mode": data.get("mode", "live"), "url": FAIRSCORE_URL}
    except Exception as e:
        logger.debug(f"FairScore service check failed: {e}")
    return {"online": False, "service": "fairscore", "url": FAIRSCORE_URL}


def check_asr_health() -> Dict[str, Any]:
    """Check if the ASR worker service is alive."""
    try:
        resp = requests.get(f"{ASR_URL}/docs", timeout=2.0)
        if resp.status_code == 200:
            return {"online": True, "service": "asr", "url": ASR_URL}
    except Exception as e:
        logger.debug(f"ASR service check failed: {e}")
    return {"online": False, "service": "asr", "url": ASR_URL}


def submit_answer_to_backend(
    session_id: str,
    question_id: str,
    question_text: str,
    answer_text: str,
    duration_sec: float = 60.0,
    force_direct: bool = False
) -> Dict[str, Any]:
    """Submit candidate answer to the backend evaluation service.
    
    If the FairScore microservice is reachable and force_direct is False,
    submits via HTTP POST /score.
    Otherwise, executes evaluation directly via the integrated pipeline.
    """
    if not force_direct:
        health = check_fairscore_health()
        if health.get("online"):
            try:
                payload = {
                    "session_id": session_id,
                    "candidate_id": "candidate_current",
                    "question_text": question_text,
                    "transcript": [
                        {
                            "start": 0.0,
                            "end": float(duration_sec),
                            "speaker": "candidate",
                            "text": answer_text
                        }
                    ]
                }
                resp = requests.post(f"{FAIRSCORE_URL}/score", json=payload, timeout=REQUEST_TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    data["execution_mode"] = "HTTP_API"
                    return data
                else:
                    logger.warning(f"Backend returned HTTP {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.warning(f"Failed to submit via API, falling back to direct pipeline: {e}")

    # Direct integrated pipeline execution
    pipeline_res = run_fairscore_pipeline(
        transcript_text=answer_text,
        question_text=question_text,
        question_id=question_id,
        duration_sec=duration_sec
    )
    pipeline_res["session_id"] = session_id
    pipeline_res["status"] = "completed"
    pipeline_res["execution_mode"] = "DIRECT_PIPELINE"
    return pipeline_res


def transcribe_audio_file(file_bytes: bytes, filename: str) -> Optional[Dict[str, Any]]:
    """Send audio file to the ASR service for transcription."""
    asr_health = check_asr_health()
    if not asr_health.get("online"):
        return None

    try:
        files = {"file": (filename, file_bytes, "audio/wav")}
        resp = requests.post(f"{ASR_URL}/transcribe", files=files, timeout=60.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"ASR transcription request failed: {e}")
    return None
