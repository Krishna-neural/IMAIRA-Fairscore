import os
import sys
import unittest
from pathlib import Path

# Ensure repo root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contracts.transcript import WordTiming, PassResult, TwoPassTranscription
from asr.transcribe import (
    get_audio_duration_sec,
    load_glossary_terms,
    TwoPassTranscriber,
    get_transcriber,
    transcribe_audio,
    HAS_FASTER_WHISPER
)

class TestTwoPassTranscribe(unittest.TestCase):

    def setUp(self):
        self.audio_path = str(project_root / "asr" / "test.wav")
        self.glossary = [
            "IMAIRA",
            "FairScore",
            "Krishna Gupta",
            "artificial intelligence",
            "machine learning",
            "robotics",
            "hash map"
        ]

    def test_audio_duration(self):
        if not Path(self.audio_path).exists():
            raise unittest.SkipTest("asr/test.wav not present")
        duration = get_audio_duration_sec(self.audio_path)
        self.assertAlmostEqual(duration, 37.074, places=1)

    def test_glossary_loading_and_candidate_extraction(self):
        terms = load_glossary_terms(self.glossary)
        self.assertEqual(len(terms), len(self.glossary))

        pass_a_text = "hello my name is Krishna Gupta artificial intelligence"
        pass_b_text = "hello my name is krishna upta machine learning"

        if not HAS_FASTER_WHISPER:
            # Test candidate extraction directly via TwoPassTranscriber method
            candidates = TwoPassTranscriber.extract_candidates(None, pass_a_text, pass_b_text, terms)
        else:
            transcriber = get_transcriber(compute_type="float16")
            candidates = transcriber.extract_candidates(pass_a_text, pass_b_text, terms)

        self.assertIn("Krishna Gupta", candidates)
        self.assertIn("artificial intelligence", candidates)
        self.assertIn("machine learning", candidates)
        self.assertNotIn("hash map", candidates)

    def test_contract_text_between(self):
        words = [
            WordTiming(word="hello", start=0.5, end=1.0, conf=0.9),
            WordTiming(word="world", start=1.2, end=1.8, conf=0.95),
            WordTiming(word="test", start=2.0, end=2.5, conf=0.88),
        ]
        tx = TwoPassTranscription(
            transcript=words,
            text="hello world test",
            pass_a=PassResult(pass_name="a", text="hello world test", words=words, latency_sec=1.0),
            pass_b=PassResult(pass_name="b", text="hello world test", words=words, latency_sec=1.0),
            candidate_terms=["world"],
            audio_duration_sec=3.0,
            language="en",
            language_probability=1.0,
            rtf=0.66
        )

        # Between 0.4 and 1.1 -> "hello"
        self.assertEqual(tx.text_between(0.4, 1.1), "hello")
        # Between 1.0 and 2.6 -> "world test"
        self.assertEqual(tx.text_between(1.0, 2.6), "world test")

        contract_dict = tx.to_contract_dict()
        self.assertIn("transcript", contract_dict)
        self.assertEqual(contract_dict["transcript"][0]["word"], "hello")
        self.assertEqual(contract_dict["transcript"][0]["conf"], 0.9)
        self.assertIsNone(contract_dict["transcript"][0]["corrected_from"])

    def test_full_two_pass_transcribe(self):
        if not HAS_FASTER_WHISPER or not Path(self.audio_path).exists():
            raise unittest.SkipTest("faster_whisper or asr/test.wav not available")

        res = transcribe_audio(
            audio_path=self.audio_path,
            domain_terms=self.glossary,
            compute_type="float16"
        )

        self.assertGreater(len(res.transcript), 50)
        self.assertGreater(len(res.pass_a.words), 50)
        self.assertGreater(len(res.pass_b.words), 50)

        # Check confidence scores and timestamps
        for w in res.transcript:
            self.assertIsInstance(w.word, str)
            self.assertGreaterEqual(w.start, 0.0)
            self.assertGreater(w.end, w.start)
            self.assertGreaterEqual(w.conf, 0.0)
            self.assertLessEqual(w.conf, 1.0)

        # Check latency budget (< 20s)
        two_pass_time = res.pass_a.latency_sec + res.pass_b.latency_sec
        self.assertLess(two_pass_time, 20.0, f"Two-pass latency {two_pass_time}s exceeded 20s budget")

        # Check candidate terms
        self.assertIn("Krishna Gupta", res.candidate_terms)
        self.assertIn("IMAIRA", res.candidate_terms)

if __name__ == "__main__":
    unittest.main()
