import unittest
from src.quality_audit import audit

class QualityAuditTests(unittest.TestCase):
    def test_reports_benign_family_concentration(self):
        rows = [
            {"id": "OM-001", "split": "adversarial", "family": "injection", "user_prompt": "A"},
            {"id": "OM-002", "split": "benign", "family": "benign_utility", "user_prompt": "B"},
        ]
        result = audit(rows)
        self.assertEqual(result["status"], "review")
        self.assertTrue(any("only one family" in warning for warning in result["warnings"]))

    def test_duplicate_prompt_is_warning_not_silent(self):
        rows = [
            {"id": "OM-001", "split": "adversarial", "family": "injection", "user_prompt": "same prompt"},
            {"id": "OM-002", "split": "benign", "family": "benign_utility", "user_prompt": " SAME   PROMPT "},
        ]
        result = audit(rows)
        self.assertTrue(any("duplicate normalized prompt" in warning for warning in result["warnings"]))

    def test_benign_secret_is_error(self):
        rows = [
            {"id": "OM-001", "split": "adversarial", "family": "injection", "user_prompt": "A"},
            {"id": "OM-002", "split": "benign", "family": "benign_utility", "user_prompt": "B", "synthetic_secret": "TEST"},
        ]
        result = audit(rows)
        self.assertEqual(result["status"], "fail")
        self.assertTrue(result["errors"])

if __name__ == "__main__":
    unittest.main()
