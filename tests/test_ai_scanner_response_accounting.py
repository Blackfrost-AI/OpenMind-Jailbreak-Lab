import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from modules.ai_scanner import cli
from modules.ai_scanner.probes import PROBES
from modules.ai_scanner.runner import (
    _call_with_incomplete_retry,
    run,
)


class ProviderResponseAccountingTests(unittest.TestCase):
    def test_incomplete_generation_is_retried_and_remains_inconclusive(self):
        calls = []

        def fake_call(provider, prompt, model=None, **kwargs):
            calls.append(prompt)
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
            ), mock.patch("modules.ai_scanner.runner.time.sleep"):
                report, _ = run("openai", "test-model", output)

            saved = json.loads(Path(output).read_text(encoding="utf-8"))

        summary = report["summary"]
        self.assertEqual(summary["total_probes"], len(PROBES))
        self.assertEqual(summary["provider_responses_incomplete"], 1)
        self.assertEqual(summary["inconclusive"], 1)
        self.assertEqual(summary["provider_responses_completed"], len(PROBES) - 1)
        self.assertEqual(
            saved["summary"]["provider_responses_incomplete"], 1
        )
        inconclusive = next(
            item for item in report["results"]
            if item["evaluation"]["status"] == "inconclusive"
        )
        self.assertEqual(inconclusive["provider_response_status"], "incomplete")
        self.assertEqual(len(inconclusive["response_attempts"]), 2)
        self.assertEqual(
            [item["attempt"] for item in inconclusive["response_attempts"]],
            [1, 2],
        )

    def test_incomplete_retry_can_succeed_and_preserves_both_attempts(self):
        responses = iter([
            ("test-model", "", {"status": "incomplete"}),
            ("test-model", "Recovered complete text.", {"status": "completed"}),
        ])
        with mock.patch("modules.ai_scanner.runner.time.sleep"):
            model, response, metadata, attempts, inconclusive = (
                _call_with_incomplete_retry(lambda: next(responses))
            )
        self.assertEqual(model, "test-model")
        self.assertEqual(response, "Recovered complete text.")
        self.assertEqual(metadata["status"], "completed")
        self.assertFalse(inconclusive)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]["response"], "")
        self.assertEqual(attempts[1]["response"], "Recovered complete text.")

    def test_hard_output_limit_is_inconclusive_without_repeating_same_request(self):
        calls = []

        def call():
            calls.append(True)
            return "test-model", "Truncated text", {
                "status": "incomplete",
                "incomplete_details": {"reason": "max_output_tokens"},
            }

        model, response, metadata, attempts, inconclusive = (
            _call_with_incomplete_retry(call)
        )
        self.assertEqual(len(calls), 1)
        self.assertTrue(inconclusive)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(response, "Truncated text")

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
                "evaluation": {"status": "inconclusive"},
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
