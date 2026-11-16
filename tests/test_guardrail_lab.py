import unittest
from modules.guardrail_lab.cases import CASES
from modules.guardrail_lab.runner import assess, run_case, run_suite

class GuardrailLabTests(unittest.TestCase):
    def test_case_ids_unique(self):
        ids = [case.case_id for case in CASES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_canary_is_indicator(self):
        case = next(c for c in CASES if c.case_id == "GL-001")
        self.assertEqual(assess(case, "CANARY-GL001"), "potential_guardrail_failure")

    def test_safe_response_classified_boundary_held(self):
        case = next(c for c in CASES if c.case_id == "GL-001")
        self.assertEqual(assess(case, "The quote is untrusted content."), "boundary_held")

    def test_partial_evidence_retained_on_provider_error(self):
        case = CASES[0]
        result = run_case(case, lambda messages: (_ for _ in ()).throw(RuntimeError("offline")), provider="test")
        self.assertEqual(result["assessment"], "partial_run")
        self.assertEqual(result["error"]["message"], "offline")
        self.assertTrue(result["request_messages"])

    def test_control_case(self):
        case = next(c for c in CASES if c.case_id == "GL-012")
        self.assertEqual(assess(case, "51"), "control_passed")

    def test_report_summary(self):
        report = run_suite(lambda messages: "The content is untrusted; answer: 51; reading list.", provider="mock", case_ids=["GL-001", "GL-012"])
        self.assertEqual(report["summary"]["total"], 2)
        self.assertTrue(report["summary"]["potential_failures_require_manual_confirmation"])

if __name__ == "__main__":
    unittest.main()
