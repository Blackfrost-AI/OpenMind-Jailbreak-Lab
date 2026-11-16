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

    def test_repository_provider_tuple_is_unpacked_and_metadata_saved(self):
        case = CASES[0]
        result = run_case(
            case,
            lambda messages: ("provider-model-1", "The quote is untrusted content.", {"request_id": "req-123", "usage": {"total_tokens": 12}}),
            provider="mock",
        )
        self.assertEqual(result["assessment"], "boundary_held")
        self.assertEqual(result["model"], "provider-model-1")
        self.assertEqual(result["provider_metadata"]["request_id"], "req-123")

    def test_control_case(self):
        case = next(c for c in CASES if c.case_id == "GL-012")
        self.assertEqual(assess(case, "51"), "control_passed")

    def test_report_summary(self):
        report = run_suite(lambda messages: "The content is untrusted; answer: 51; reading list.", provider="mock", case_ids=["GL-001", "GL-012"])
        self.assertEqual(report["summary"]["total"], 2)
        self.assertTrue(report["summary"]["potential_failures_require_manual_confirmation"])

    def test_duplicate_case_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate case IDs"):
            run_suite(lambda messages: "ok", provider="mock", case_ids=["GL-001", "GL-001"])

    def test_followup_requires_setup_case_immediately_before_it(self):
        with self.assertRaisesRegex(ValueError, "GL-009"):
            run_suite(lambda messages: "ok", provider="mock", case_ids=["GL-010"])
        with self.assertRaisesRegex(ValueError, "GL-009"):
            run_suite(lambda messages: "ok", provider="mock", case_ids=["GL-001", "GL-010"])

class ReportAndCliTests(unittest.TestCase):
    def test_write_report_creates_parent_directory(self):
        import json
        import tempfile
        from pathlib import Path
        from modules.guardrail_lab.runner import write_report

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "nested" / "reports" / "result.json"
            write_report({"ok": True}, str(target))
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), {"ok": True})

    def test_list_does_not_require_provider(self):
        from contextlib import redirect_stdout
        from io import StringIO
        from modules.guardrail_lab.cli import main

        output = StringIO()
        with redirect_stdout(output):
            status = main(["--list"])
        self.assertEqual(status, 0)
        self.assertIn("GL-001", output.getvalue())


if __name__ == "__main__":
    unittest.main()
