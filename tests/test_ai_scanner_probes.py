import unittest
from modules.ai_scanner.probes import PROBES, evaluate


class ProbeEvaluationTests(unittest.TestCase):
    def test_canary_match_is_potential_failure(self):
        probe = next(
            p for p in PROBES
            if p["id"] == "BOUNDARY-001"
        )
        result = evaluate(
            probe,
            "Observed CANARY_OVERRIDE_7F31",
        )
        self.assertEqual(
            result["status"],
            "potential_failure",
        )

    def test_no_canary_is_not_a_security_pass(self):
        probe = next(
            p for p in PROBES
            if p["id"] == "BOUNDARY-001"
        )
        result = evaluate(
            probe,
            "I will summarize the note.",
        )
        self.assertEqual(
            result["status"],
            "no_indicator_observed",
        )

    def test_qualitative_probe_requires_review(self):
        probe = next(
            p for p in PROBES
            if p["id"] == "DISCLOSURE-001"
        )
        result = evaluate(
            probe,
            "I cannot provide that.",
        )
        self.assertEqual(
            result["status"],
            "manual_review",
        )


if __name__ == "__main__":
    unittest.main()
