import sys
import unittest
from pathlib import Path

# Ensure repo root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contracts.transcript import (
    WordTiming,
    SuspiciousSpan,
    RecoveryResult,
    RecoveryAuditEntry
)
from asr.span_detector import SuspiciousSpanDetector
from asr.recover import AudioRecoveryPipeline, recover_transcript
from faster_whisper.audio import decode_audio

class TestAudioRecovery(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.audio_path = str(project_root / "asr" / "test.wav")
        cls.pipeline = AudioRecoveryPipeline(compute_type="float16")
        cls.audio_data = decode_audio(cls.audio_path)
        cls.duration = len(cls.audio_data) / 16000.0

    def test_recheck_supported_span(self):
        # Krishna Gupta span at [1.56s - 2.08s]
        span_gupta = SuspiciousSpan(
            span_id="span_test_gupta",
            start_idx=4,
            end_idx=6,
            t_start=1.56,
            t_end=2.08,
            original_text="krishna upta",
            candidate_term="Krishna Gupta",
            avg_conf=0.71,
            min_conf=0.69,
            fuzzy_score=96.0,
            phonetic_match=True,
            combined_score=95.0,
            reason="alias_match"
        )

        supported, redec_text, conf, reason = self.pipeline.recheck_span(
            audio_data=self.audio_data,
            duration_sec=self.duration,
            span=span_gupta
        )

        self.assertTrue(supported, f"Audio should support 'Krishna Gupta'. Reason: {reason}, redec: '{redec_text}'")
        self.assertEqual(reason, "audio_supported")
        self.assertIn("krishna gupta", redec_text.lower())

    def test_recheck_unsupported_span_abstains(self):
        # False candidate 'A/B testing' at [2.08s - 2.54s] where speaker actually said 'i am testing'
        span_false = SuspiciousSpan(
            span_id="span_test_false",
            start_idx=6,
            end_idx=8,
            t_start=2.08,
            t_end=2.54,
            original_text="i'm testing",
            candidate_term="A/B testing",
            avg_conf=0.82,
            min_conf=0.80,
            fuzzy_score=81.8,
            phonetic_match=False,
            combined_score=81.8,
            reason="low_conf_glossary"
        )

        supported, redec_text, conf, reason = self.pipeline.recheck_span(
            audio_data=self.audio_data,
            duration_sec=self.duration,
            span=span_false
        )

        self.assertFalse(supported, "Pipeline should ABSTAIN from falsely correcting 'i am testing' to 'A/B testing'")
        self.assertEqual(reason, "audio_not_supported")

    def test_end_to_end_recovery_and_audit(self):
        res = recover_transcript(self.audio_path, compute_type="float16")

        self.assertIsInstance(res, RecoveryResult)
        self.assertGreaterEqual(res.spans_detected, 2)
        self.assertGreaterEqual(res.spans_corrected, 1)
        self.assertGreaterEqual(res.spans_abstained, 1)

        # Ensure correct term present and false term absent in corrected text
        self.assertIn("Krishna Gupta", res.corrected_text)
        self.assertNotIn("A/B testing", res.corrected_text)

        # Original text must preserve pristine baseline
        self.assertIn("krishna upta", res.original_text)

        # Check audit log structure
        corrected_entries = [e for e in res.audit_log if e.decision == "CORRECTED"]
        abstained_entries = [e for e in res.audit_log if e.decision == "ABSTAINED"]
        self.assertGreaterEqual(len(corrected_entries), 1)
        self.assertGreaterEqual(len(abstained_entries), 1)

        # Verify WordTiming corrected_from field
        corrected_words = [w for w in res.corrected_transcript if w.corrected_from is not None]
        self.assertGreaterEqual(len(corrected_words), 1)
        self.assertEqual(corrected_words[0].word, "Krishna")
        self.assertEqual(corrected_words[0].corrected_from, "krishna")

        # Verify latency within budget (< 20s)
        self.assertLess(res.recovery_latency_sec, 20.0)

        # Verify contract serialization
        contract = res.to_contract_dict()
        self.assertIn("transcript", contract)
        self.assertIn("audit_log", contract)
        self.assertEqual(contract["spans_corrected"], res.spans_corrected)

if __name__ == "__main__":
    unittest.main()
