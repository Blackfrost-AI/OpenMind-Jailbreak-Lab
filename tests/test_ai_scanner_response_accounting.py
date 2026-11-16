import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from modules.ai_scanner import cli
from modules.ai_scanner.probes import PROBES
from modules.ai_scanner.runner import run


class ProviderResponseAccountingTests(unittest.TestCase):
    def test_empty_incomplete_generation_is_not_counted_as_completed(self):
        def fake_call(provider, prompt, model=None, **kwargs):
            if "safe, bounded test approach" in prompt:
                return "test-model", "", {"status": "incomplete"}
            return "test-model", "A normal response.", {"status": "completed"}

        def fake_messages(provider, messages, model=None, **kwargs):
            return "test-model", "A normal response.", {"status": "completed"}

        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "report.json")
            with mock.patch(
                "modules.ai_scanner.runner.call_provider",
                side_effect=fake_call,
            ), mock.patch(
                "modules.ai_scanner.runner.call_provider_messages",
                side_effect=fake_messages,
            ):
                report, _ = run("openai", "test-model", output)

            saved = json.loads(Path(output).read_text(encoding="utf-8"))

        summary = report["summary"]
        self.assertEqual(summary["total_probes"], len(PROBES))
        # Probe execution and provider response completion are separate.
        self.assertEqual(summary["probe_executions_completed"], len(PROBES))
        self.assertEqual(summary["provider_responses_completed"], len(PROBES) - 1)
        self.assertEqual(summary["provider_responses_incomplete"], 1)
        self.assertEqual(summary["provider_responses_empty"], 0)
        self.assertEqual(summary["provider_responses_not_received"], 0)
        self.assertEqual(
            saved["summary"]["provider_responses_incomplete"], 1
        )
        incomplete = next(
            item for item in report["results"]
            if item["evaluation"]["status"] == "empty_response"
        )
        self.assertEqual(incomplete["provider_response_status"], "incomplete")
        self.assertEqual(incomplete["evaluation"]["status"], "empty_response")

    def test_empty_body_without_provider_incomplete_status_is_empty(self):
        from modules.ai_scanner.runner import _provider_response_status

        self.assertEqual(_provider_response_status("", {}, None), "empty")
        self.assertEqual(
            _provider_response_status("some text", {"status": "incomplete"}, None),
            "incomplete",
        )
        self.assertEqual(
            _provider_response_status("some text", {"finish_reason": "length"}, None),
            "incomplete",
        )
        self.assertEqual(
            _provider_response_status(None, {}, RuntimeError("network")),
            "not_received",
        )

    def test_cli_returns_nonzero_for_incomplete_provider_response(self):
        report = {
            "results": [{
                "evaluation": {"status": "empty_response"},
                "provider_response_status": "incomplete",
                "error": None,
            }]
        }
        with mock.patch("modules.ai_scanner.cli.run", return_value=(report, "report.json")):
            self.assertEqual(
                cli.main(["--provider", "openai", "--output", "report.json"]),
                1,
            )


if __name__ == "__main__":
    unittest.main()
