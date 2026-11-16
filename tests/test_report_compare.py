import unittest
from modules.guardrail_lab.compare import compare_reports

class ReportComparisonTests(unittest.TestCase):
    def test_compares_common_cases_and_surfaces_missing_cases(self):
        a = {"provider": "alpha", "model": "a1", "results": [
            {"case_id": "GL-001", "assessment": "boundary_held"},
            {"case_id": "GL-002", "assessment": "manual_review"},
        ]}
        b = {"provider": "beta", "model": "b1", "results": [
            {"case_id": "GL-001", "assessment": "boundary_held"},
            {"case_id": "GL-003", "assessment": "partial_run"},
        ]}
        result = compare_reports([a, b])
        self.assertEqual(result["common_case_count"], 1)
        self.assertEqual(result["agreement_rate_on_common_cases"], 1.0)
        self.assertEqual(result["missing_case_ids"]["alpha/a1"], ["GL-003"])
        self.assertEqual(result["missing_case_ids"]["beta/b1"], ["GL-002"])

    def test_disagreement_is_not_hidden(self):
        a = {"provider": "alpha", "results": [{"case_id": "GL-001", "assessment": "boundary_held"}]}
        b = {"provider": "beta", "results": [{"case_id": "GL-001", "assessment": "manual_review"}]}
        result = compare_reports([a, b])
        self.assertEqual(result["agreement_rate_on_common_cases"], 0.0)
        self.assertEqual(result["disagreement_or_missing_case_ids"], ["GL-001"])

    def test_duplicate_provider_model_labels_rejected(self):
        report = {"provider": "same", "model": "m1", "results": [{"case_id": "GL-001"}]}
        with self.assertRaisesRegex(ValueError, "duplicate provider/model"):
            compare_reports([report, report])

    def test_duplicate_case_ids_rejected(self):
        report = {"results": [{"case_id": "GL-001"}, {"case_id": "GL-001"}]}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compare_reports([report, report])

if __name__ == "__main__":
    unittest.main()
