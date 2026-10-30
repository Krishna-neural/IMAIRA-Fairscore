import pytest
from api.main import (
    start_interview_session,
    process_interview_turn,
    conclude_interview,
    get_interview_session,
    get_fairness_audit,
    get_latency_metrics,
    StartInterviewRequest,
    InterviewTurnRequest,
    ConcludeInterviewRequest,
)


def test_full_lifecycle_interview_flow_with_dual_diagnosis_and_conclusion():
    # 1. Start interview
    start_data = start_interview_session(
        StartInterviewRequest(
            candidate_name="Rupesh",
            domain="Systems & Database Architecture",
            difficulty="Intermediate",
            num_questions=2,
        )
    )
    session_id = start_data["session_id"]
    assert session_id.startswith("sess_")
    assert "greeting" in start_data
    assert start_data["first_question"] is not None

    # 2. Greeting Turn response
    greet_data = process_interview_turn(
        InterviewTurnRequest(
            session_id=session_id,
            candidate_utterance="Hello, I am ready to begin the systems architecture interview.",
        )
    )
    assert greet_data["status"] == "success"
    assert greet_data["session_id"] == session_id
    assert greet_data["is_concluded"] is False
    assert "Thank you" in greet_data["ai_response"]

    # 3. Technical Question Turn with phonetic slip ("semfor", "cubernetes")
    turn1_data = process_interview_turn(
        InterviewTurnRequest(
            session_id=session_id,
            candidate_utterance="In distributed microservices, thread execution lock is governed by a semfor primitive and container orchestration runs on cubernetes clusters.",
        )
    )
    assert turn1_data["status"] == "success"
    # Verify acoustic slice recovery occurred
    assert "semaphore" in turn1_data["recovered_utterance"]
    assert "Kubernetes" in turn1_data["recovered_utterance"]
    assert turn1_data["corrections_applied"] >= 2
    # Verify silent evaluation was attached
    assert "evaluation" in turn1_data
    if turn1_data["evaluation"]:
        eval_obj = turn1_data["evaluation"]
        assert "scores" in eval_obj
        assert "dual_diagnosis" in eval_obj
        pronounce_list = eval_obj["dual_diagnosis"].get("pronunciation_improvements", [])
        assert len(pronounce_list) >= 1
        # Marks deducted for accent MUST be 0.0
        for p in pronounce_list:
            assert p["marks_deducted"] == 0.0

    # 4. Conclude Interview via conclude_interview
    conclude_data = conclude_interview(
        ConcludeInterviewRequest(session_id=session_id)
    )
    assert conclude_data["status"] == "completed"
    assert conclude_data["stage"] == "COMPLETED"
    scorecard = conclude_data["final_scorecard"]
    assert scorecard is not None
    assert "overall_fairscore" in scorecard
    assert "cumulative_dual_diagnosis" in scorecard

    dual = scorecard["cumulative_dual_diagnosis"]
    assert dual["accent_penalty_applied"] is False
    assert dual["acoustic_protection_active"] is True
    # Pronunciation improvement suggestions should be present
    assert len(dual["pronunciation_improvements"]) >= 1

    # 5. Retrieve full persistent session from get_interview_session
    sess_data = get_interview_session(session_id)
    assert sess_data["session_id"] == session_id
    assert sess_data["stage"] == "COMPLETED"
    assert len(sess_data["turns"]) >= 2
    assert sess_data["final_scorecard"] is not None


def test_fairness_audit_and_latency_endpoints():
    # Test get_fairness_audit
    audit_data = get_fairness_audit()
    assert (
        "status" in audit_data
        or "target" in audit_data
        or "dimensions" in audit_data
        or "robustness_summary" in audit_data
    )

    # Test get_latency_metrics
    lat_data = get_latency_metrics()
    assert "stage2_glossary_verification_latency_ms" in lat_data
