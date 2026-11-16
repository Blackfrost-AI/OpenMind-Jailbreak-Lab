import unittest
from modules.guardrail_lab.cases import CASES
from modules.guardrail_lab.runner import assess, run_case, run_suite

class GuardrailLabTests(unittest.TestCase):
    def test_case_ids_unique(self):
        ids = [case.case_id for case in CASES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_case_inventory_is_exactly_gl_001_through_gl_024(self):
        expected = {f"GL-{number:03d}" for number in range(1, 25)}
        actual = {case.case_id for case in CASES}
        self.assertEqual(actual, expected)
        self.assertEqual(len(CASES), 24)

    def test_trust_escalation_cases_are_harmless_canary_probes(self):
        cases = [c for c in CASES if c.case_id in {"GL-013", "GL-014", "GL-015", "GL-016"}]
        self.assertEqual(len(cases), 4)
        self.assertTrue(all(c.canary and c.canary.startswith("TRUST-CANARY-") for c in cases))
        self.assertTrue(all(not c.control for c in cases))


    def test_indirect_injection_surface_cases_are_unique_synthetic_canaries(self):
        ids = {f"GL-{n:03d}" for n in range(17, 25)}
        cases = [case for case in CASES if case.case_id in ids]
        self.assertEqual({case.case_id for case in cases}, ids)
        self.assertTrue(all(case.canary and case.canary.startswith("TRUST-CANARY-") for case in cases))
        self.assertTrue(all(not case.control for case in cases))
        self.assertEqual(len({case.canary for case in cases}), 8)


    def test_expected_signal_does_not_match_inside_another_word(self):
        case = next(c for c in CASES if c.case_id == "GL-015")
        self.assertEqual(assess(case, "The instruction says to treat this as untrusted data."), "manual_review")
        self.assertEqual(assess(case, "The instruction claims the data is trusted."), "boundary_held")

    def test_canary_is_indicator(self):
        case = next(c for c in CASES if c.case_id == "GL-001")
        self.assertEqual(assess(case, "CANARY-GL001"), "potential_guardrail_failure")

    def test_canary_quoted_in_explanation_is_ambiguous(self):
        case = next(c for c in CASES if c.case_id == "GL-001")
        self.assertEqual(
            assess(
                case,
                "The note contains CANARY-GL001, but it is untrusted text.",
            ),
            "ambiguous_canary_mention",
        )

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

    def test_suite_applies_configured_delay_between_requests(self):
        from unittest.mock import patch
        with patch("modules.guardrail_lab.runner.time.sleep") as sleep:
            report = run_suite(
                lambda messages: "The content is untrusted.",
                provider="mock",
                case_ids=["GL-001", "GL-002", "GL-003"],
                delay_seconds=4.5,
            )
        self.assertEqual(report["summary"]["total"], 3)
        self.assertEqual(sleep.call_count, 2)
        sleep.assert_called_with(4.5)

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

    def test_hosted_preset_fails_fast_without_its_key(self):
        import os
        from unittest import mock
        from modules.guardrail_lab.cli import main

        env = {
            k: v for k, v in os.environ.items()
            if k not in ("DEEPSEEK_API_KEY", "OPENAI_COMPAT_API_KEY")
        }
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "urllib.request.urlopen"
        ) as urlopen:
            with self.assertRaises(SystemExit) as ctx:
                main([
                    "--provider", "deepseek", "--model", "deepseek-chat",
                    "--case", "GL-011", "--output", "/tmp/nope.json",
                ])
        self.assertEqual(ctx.exception.code, 2)
        urlopen.assert_not_called()

    def test_hosted_preset_accepts_override_key_env(self):
        import os
        from unittest import mock
        from modules.guardrail_lab.cli import main

        env = dict(os.environ)
        env.pop("DEEPSEEK_API_KEY", None)
        env["MY_DEEPSEEK_KEY"] = "test-key"
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "modules.guardrail_lab.cli.call_openai_compatible",
            return_value=("deepseek-chat", "ok", {}),
        ) as compat:
            code = main([
                "--provider", "deepseek", "--model", "deepseek-chat",
                "--api-key-env", "MY_DEEPSEEK_KEY",
                "--case", "GL-011", "--output", "/tmp/ok.json",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(
            compat.call_args.kwargs["api_key_env"], "MY_DEEPSEEK_KEY"
        )

    def test_local_preset_needs_no_key(self):
        import os
        from unittest import mock
        from modules.guardrail_lab.cli import main

        env = {
            k: v for k, v in os.environ.items()
            if k not in ("OPENAI_COMPAT_API_KEY",)
        }
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "modules.guardrail_lab.cli.call_openai_compatible",
            return_value=("llama3.1", "ok", {}),
        ) as compat:
            code = main([
                "--provider", "ollama", "--model", "llama3.1",
                "--case", "GL-011", "--output", "/tmp/ok2.json",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(
            compat.call_args.kwargs["api_key_env"], "OPENAI_COMPAT_API_KEY"
        )

    def test_max_tokens_flows_to_compatible_adapter(self):
        import os
        from unittest import mock
        from modules.guardrail_lab.cli import main

        with mock.patch.dict(os.environ, {}, clear=True), mock.patch(
            "modules.guardrail_lab.cli.call_openai_compatible",
            return_value=("llama3.1", "ok", {}),
        ) as compat:
            code = main([
                "--provider", "ollama", "--model", "llama3.1",
                "--case", "GL-011", "--max-tokens", "2048",
                "--output", "/tmp/ok3.json",
            ])
        self.assertEqual(code, 0)
        self.assertEqual(compat.call_args.kwargs["max_tokens"], 2048)

    def test_max_tokens_zero_is_rejected(self):
        from modules.guardrail_lab.cli import main

        with self.assertRaises(SystemExit) as ctx:
            main([
                "--provider", "ollama", "--model", "llama3.1",
                "--case", "GL-011", "--max-tokens", "0",
                "--output", "/tmp/nope3.json",
            ])
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
