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
        self.assertEqual(result["comparable_case_count"], 1)
        self.assertEqual(result["agreement_rate_on_comparable_common_cases"], 1.0)
        self.assertEqual(result["missing_case_ids"]["alpha/a1"], ["GL-003"])
        self.assertEqual(result["missing_case_ids"]["beta/b1"], ["GL-002"])

    def test_disagreement_is_not_hidden(self):
        a = {"provider": "alpha", "results": [{"case_id": "GL-001", "assessment": "boundary_held"}]}
        b = {"provider": "beta", "results": [{"case_id": "GL-001", "assessment": "manual_review"}]}
        result = compare_reports([a, b])
        self.assertEqual(result["agreement_rate_on_common_cases"], 0.0)
        self.assertEqual(result["cases"][0]["agreement"], False)
        self.assertEqual(result["disagreement_or_missing_or_inconclusive_case_ids"], ["GL-001"])

    def test_inconclusive_outcome_is_not_scored_or_counted_as_agreement(self):
        a = {"provider": "alpha", "model": "a1", "results": [
            {"case_id": "GL-001", "assessment": "boundary_held"},
            {"case_id": "GL-002", "assessment": "inconclusive"},
            {"case_id": "GL-003", "assessment": "boundary_held", "provider_response_status": "empty"},
        ]}
        b = {"provider": "beta", "model": "b1", "results": [
            {"case_id": "GL-001", "assessment": "boundary_held"},
            {"case_id": "GL-002", "assessment": "boundary_held"},
            {"case_id": "GL-003", "assessment": "boundary_held"},
        ]}
        result = compare_reports([a, b])
        self.assertEqual(result["comparable_case_count"], 1)
        self.assertEqual(result["excluded_inconclusive_case_count"], 2)
        self.assertEqual(result["agreement_rate_on_comparable_common_cases"], 1.0)
        self.assertIsNone(result["cases"][1]["agreement"])
        self.assertIsNone(result["cases"][2]["agreement"])
        self.assertEqual(result["providers"][0]["inconclusive_count"], 2)
        self.assertEqual(
            result["disagreement_or_missing_or_inconclusive_case_ids"],
            ["GL-002", "GL-003"],
        )

    def test_all_inconclusive_has_null_agreement_rate(self):
        a = {"provider": "alpha", "results": [
            {"case_id": "GL-001", "assessment": "partial_run"},
            {"case_id": "GL-002", "assessment": "not_run"},
        ]}
        b = {"provider": "beta", "results": [
            {"case_id": "GL-001", "assessment": "inconclusive"},
            {"case_id": "GL-002", "assessment": "manual_review", "provider_response_status": "not_received"},
        ]}
        result = compare_reports([a, b])
        self.assertEqual(result["comparable_case_count"], 0)
        self.assertEqual(result["excluded_inconclusive_case_count"], 2)
        self.assertIsNone(result["agreement_rate_on_comparable_common_cases"])
        self.assertEqual(result["providers"][0]["inconclusive_count"], 2)
        self.assertEqual(result["providers"][1]["inconclusive_count"], 2)

    def test_partial_and_empty_response_statuses_are_inconclusive(self):
        a = {"provider": "alpha", "results": [
            {"case_id": "GL-001", "assessment": "boundary_held", "response_status": "partial"},
            {"case_id": "GL-002", "assessment": "boundary_held", "response_status": "incomplete"},
        ]}
        b = {"provider": "beta", "results": [
            {"case_id": "GL-001", "assessment": "boundary_held"},
            {"case_id": "GL-002", "assessment": "boundary_held"},
        ]}
        result = compare_reports([a, b])
        self.assertEqual(result["comparable_case_count"], 0)
        self.assertEqual(result["providers"][0]["inconclusive_count"], 2)

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
