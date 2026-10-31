"""Unit and integration test suite for Stage 3: Real-Time ASR & Acoustic Slice Recovery Integration.

Validates streaming audio chunks, phonetic & glossary slice recovery,
conservative acoustic abstention, audio persistence, and WebSocket transport.
"""

import base64
import os
import shutil
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent

from asr.stream_bridge import StreamTranscriptionBridge
from asr.span_detector import SuspiciousSpanDetector
from api.main import (
    app,
    start_interview_session,
    process_interview_turn,
    get_interview_session,
    StartInterviewRequest,
    InterviewTurnRequest,
    session_manager,
)


@pytest.fixture
def stream_bridge():
    return StreamTranscriptionBridge()


# ==============================================================================
# 1. Real-Time Streaming & Provisional Hypotheses
# ==============================================================================

def test_streaming_provisional_chunks(stream_bridge):
    """Verify sub-50ms latency and word count tracking for live incremental chunks."""
    res = stream_bridge.process_live_chunk("We are designing a distributed")
    assert res["status"] == "provisional"
    assert res["provisional_text"] == "We are designing a distributed"
    assert res["word_count"] == 5
    assert res["latency_ms"] < 50.0


# ==============================================================================
# 2. Phonetic & Glossary Acoustic Slice Recovery (Known Accent Slips)
# ==============================================================================

@pytest.mark.parametrize("raw_input,expected_keyword", [
    ("We store session data in a has map for O(1) retrieval.", "hash map"),
    ("Thread execution lock is governed by a semfor primitive.", "semaphore"),
    ("The primary datastore runs on postgress in production.", "PostgreSQL"),
    ("Microservices are orchestrated in cubernetes clusters.", "Kubernetes"),
    ("Distributed cache is backed by reddis cluster.", "Redis"),
    ("We maintain node pointers in a link list data structure.", "linked list"),
    ("Non blocking operations use asink callbacks.", "async"),
])
def test_accent_recovery_known_confusions(stream_bridge, raw_input, expected_keyword):
    """Verify non-native accent slips are automatically recovered against glossary."""
    res = stream_bridge.finalize_and_verify(raw_input)
    assert expected_keyword.lower() in res["verified_transcript"].lower(), (
        f"Expected '{expected_keyword}' in '{res['verified_transcript']}'"
    )
    assert res["corrections_applied"] >= 1
    assert any(log["status"] == "CORRECTED" for log in res["audit_log"])


def test_inflection_and_caching_protection(stream_bridge):
    """Verify valid technical terms and their inflections (e.g. caching, threads) are never corrupted."""
    text = "The database runs on postgress with reddis caching and worker threads."
    res = stream_bridge.finalize_and_verify(text)
    verified = res["verified_transcript"]

    # Corrections applied to actual misrecognitions
    assert "PostgreSQL" in verified
    assert "Redis" in verified

    # Valid technical words MUST NOT be corrupted
    assert "caching" in verified
    assert "threads" in verified


# ==============================================================================
# 3. Conservative Acoustic Abstention Invariant
# ==============================================================================

def test_conservative_acoustic_abstention(stream_bridge):
    """Verify clean technical sentences with standard English words trigger ZERO false corrections."""
    clean_text = "The quick brown fox jumps over the lazy dog and optimizes binary search trees."
    res = stream_bridge.finalize_and_verify(clean_text)

    # Should not corrupt standard English words
    assert "quick" in res["verified_transcript"]
    assert "brown" in res["verified_transcript"]
    assert "fox" in res["verified_transcript"]
    assert "lazy" in res["verified_transcript"]
    assert "dog" in res["verified_transcript"]
    assert "binary search" in res["verified_transcript"]


# ==============================================================================
# 4. Audio Byte Ingestion & Persistence
# ==============================================================================

def test_audio_byte_ingestion_and_file_persistence():
    """Verify audio base64 is decoded, persisted to artifacts/audio/, and logged in TurnRecord."""
    # 1. Start session
    start_req = StartInterviewRequest(
        candidate_name="Margaret Hamilton",
        domain="Software and Computer Science Fundamentals",
        difficulty="Intermediate",
        num_questions=1
    )
    start_res = start_interview_session(start_req)
    sess_id = start_res["session_id"]

    # 2. Fake small WAV header (44 bytes standard PCM header)
    fake_wav_bytes = b"RIFF" + b"\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    b64_audio = base64.b64encode(fake_wav_bytes).decode("utf-8")

    # 3. Submit turn with audio
    turn_res = process_interview_turn(InterviewTurnRequest(
        session_id=sess_id,
        candidate_utterance="Hello, I specialize in real-time fault tolerant systems.",
        audio_base64=b64_audio
    ))

    assert turn_res["stage"] == "TECHNICAL_QUESTION"

    # 4. Verify turn record in SQLite has audio_path
    sess = session_manager.get_session(sess_id)
    assert sess is not None
    assert len(sess.turns) >= 2  # Turn 1: greeting, Turn 2: candidate
    candidate_turns = [t for t in sess.turns if t.speaker == "candidate"]
    assert len(candidate_turns) == 1
    c_turn = candidate_turns[0]
    assert c_turn.audio_path is not None
    assert Path(c_turn.audio_path).exists()


# ==============================================================================
# 5. Full End-to-End Turn with Real-Time Accent Slice Recovery
# ==============================================================================

def test_interview_turn_realtime_slice_recovery():
    """Verify candidate answer with accent slip is recovered live and tracked in turn response."""
    start_req = StartInterviewRequest(
        candidate_name="Rupesh Sharma",
        domain="Software and Computer Science Fundamentals",
        difficulty="Intermediate",
        num_questions=2
    )
    start_res = start_interview_session(start_req)
    sess_id = start_res["session_id"]

    # Candidate says "has map" and "semfor"
    turn_res = process_interview_turn(InterviewTurnRequest(
        session_id=sess_id,
        candidate_utterance="We resolve collisions in a has map and synchronize threads using a semfor."
    ))

    assert turn_res["raw_utterance"] == "We resolve collisions in a has map and synchronize threads using a semfor."
    assert "hash map" in turn_res["recovered_utterance"]
    assert "semaphore" in turn_res["recovered_utterance"]
    assert turn_res["corrections_applied"] == 2
    assert len(turn_res["slice_recovery_log"]) == 2

    # Verify persistent DB contains the recovered utterance and audit log
    sess_detail = get_interview_session(sess_id)
    cand_turns = [t for t in sess_detail["turns"] if t["speaker"] == "candidate"]
    assert len(cand_turns) == 1
    assert "hash map" in cand_turns[0]["recovered_utterance"]
    assert len(cand_turns[0]["slice_recovery_log"]) == 2


# ==============================================================================
# 6. WebSocket Bidirectional Streaming Transport
# ==============================================================================

def test_websocket_streaming_transport():
    """Verify bidirectional WebSocket handles chunks, finalization with recovery, and ping/pong."""
    import json
    from fastapi import WebSocketDisconnect
    from api.main import websocket_stream_endpoint

    def step_coro(coro):
        stack = [coro]
        res = None
        while stack:
            try:
                sub = stack[-1].send(None)
                if hasattr(sub, "send"):
                    stack.append(sub)
            except StopIteration as e:
                res = e.value
                stack.pop()
        return res

    class MockWebSocket:
        def __init__(self):
            self.sent = []
            self.items = [
                json.dumps({"type": "ping"}),
                json.dumps({"type": "chunk", "text": "We store data in a"}),
                json.dumps({"type": "finalize", "text": "We store data in a has map"}),
            ]
        async def accept(self):
            pass
        async def receive_text(self):
            if self.items:
                return self.items.pop(0)
            raise WebSocketDisconnect(1000)
        async def send_text(self, text):
            self.sent.append(json.loads(text))

    mock_ws = MockWebSocket()
    step_coro(websocket_stream_endpoint(mock_ws))

    assert len(mock_ws.sent) == 3
    # 1. Ping / Pong
    assert mock_ws.sent[0]["type"] == "pong"

    # 2. Live provisional chunk
    assert mock_ws.sent[1]["type"] == "provisional"
    assert mock_ws.sent[1]["text"] == "We store data in a"
    assert mock_ws.sent[1]["word_count"] == 5

    # 3. Finalize utterance with accent recovery
    assert mock_ws.sent[2]["type"] == "verified"
    assert mock_ws.sent[2]["original_transcript"] == "We store data in a has map"
    assert "hash map" in mock_ws.sent[2]["verified_transcript"]
    assert mock_ws.sent[2]["corrections_applied"] >= 1
    assert len(mock_ws.sent[2]["audit_log"]) >= 1
