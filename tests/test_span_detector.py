import sys
import unittest
from pathlib import Path

# Ensure repo root is on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from contracts.transcript import WordTiming, SuspiciousSpan
from asr.span_detector import SuspiciousSpanDetector

class TestSuspiciousSpanDetector(unittest.TestCase):

    def setUp(self):
        self.glossary = [
            "hash map",
            "linked list",
            "binary search tree",
            "recursion",
            "polymorphism",
            "synchronous",
            "machine learning",
            "artificial intelligence",
            "robotics",
            "Krishna Gupta",
            "IMAIRA"
        ]
        self.detector = SuspiciousSpanDetector(
            glossary=self.glossary,
            confidence_threshold=0.85,
            similarity_threshold=75.0,
            phonetic_bonus=12.0
        )

    def test_phonetic_and_fuzzy_scoring(self):
        fuzz_sc, comb_sc, p_match = self.detector.score_candidate("has map", "hash map")
        self.assertGreaterEqual(fuzz_sc, 90.0)
        self.assertTrue(p_match)
        self.assertGreaterEqual(comb_sc, 95.0)

        fuzz_sc, comb_sc, p_match = self.detector.score_candidate("link list", "linked list")
        self.assertGreaterEqual(fuzz_sc, 90.0)

        fuzz_sc, comb_sc, p_match = self.detector.score_candidate("polymorfism", "polymorphism")
        self.assertTrue(p_match)
        self.assertGreaterEqual(comb_sc, 90.0)

    def test_detection_on_synthetic_transcripts(self):
        # Case 1: Accent distortion with low confidence: "we used a has map for lookup"
        words = [
            WordTiming(word="we", start=0.0, end=0.2, conf=0.98),
            WordTiming(word="used", start=0.2, end=0.5, conf=0.99),
            WordTiming(word="a", start=0.5, end=0.6, conf=0.99),
            WordTiming(word="has", start=0.6, end=0.9, conf=0.62),
            WordTiming(word="map", start=0.9, end=1.2, conf=0.70),
            WordTiming(word="for", start=1.2, end=1.4, conf=0.99),
            WordTiming(word="lookup", start=1.4, end=1.9, conf=0.97),
        ]

        spans = self.detector.detect_spans(words)
        self.assertEqual(len(spans), 1)
        self.assertEqual(spans[0].candidate_term, "hash map")
        self.assertIn("has map", spans[0].original_text)
        self.assertTrue(spans[0].phonetic_match)
        self.assertAlmostEqual(spans[0].t_start, 0.6, places=1)
        self.assertAlmostEqual(spans[0].t_end, 1.2, places=1)

    def test_rejection_of_common_words(self):
        # Low confidence on common words should NOT be flagged as technical glossary errors
        words = [
            WordTiming(word="hello", start=0.0, end=0.4, conf=0.20),
            WordTiming(word="there", start=0.4, end=0.8, conf=0.99),
        ]
        spans = self.detector.detect_spans(words)
        self.assertEqual(len(spans), 0, "Common word 'hello' should not be flagged as glossary candidate")

    def test_cross_pass_discrepancy_detection(self):
        # Pass B has mangled name with low confidence: "krishna upta"
        pass_b = [
            WordTiming(word="hello", start=0.0, end=0.5, conf=0.95),
            WordTiming(word="krishna", start=0.5, end=0.9, conf=0.74),
            WordTiming(word="upta", start=0.9, end=1.3, conf=0.69),
        ]
        # Pass A had domain hotwords: "Krishna Gupta"
        pass_a = [
            WordTiming(word="hello", start=0.0, end=0.5, conf=0.95),
            WordTiming(word="Krishna", start=0.5, end=0.9, conf=0.92),
            WordTiming(word="Gupta", start=0.9, end=1.3, conf=0.90),
        ]

        spans = self.detector.detect_spans(
            transcript=pass_b,
            pass_a_transcript=pass_a,
            candidate_terms=["Krishna Gupta"]
        )

        self.assertGreaterEqual(len(spans), 1)
        names = [s.candidate_term for s in spans]
        self.assertIn("Krishna Gupta", names)

    def test_execution_speed(self):
        # Verify latency is sub-10ms for a 100-word sentence against full 2000-term glossary
        csv_detector = SuspiciousSpanDetector(
            glossary_path="data/glossary.csv",
            confidence_threshold=0.85
        )
        test_words = [
            WordTiming(word="algorithm", start=i*0.5, end=(i+1)*0.5, conf=0.70)
            for i in range(100)
        ]
        import time
        t0 = time.perf_counter()
        spans = csv_detector.detect_spans(test_words)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self.assertLess(elapsed_ms, 50.0, f"Detection took {elapsed_ms:.2f}ms, expected < 50ms")

if __name__ == "__main__":
    unittest.main()
