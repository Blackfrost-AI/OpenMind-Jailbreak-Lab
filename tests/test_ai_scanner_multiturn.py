import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from modules.ai_scanner.probes import PROBES, evaluate
from modules.ai_scanner.providers import ProviderError, call_provider, call_provider_messages
from modules.ai_scanner.runner import run

LIVE_PROBE_ID = "MULTITURN-LIVE-001"


class MessageCallTests(unittest.TestCase):
    def _body_for(self, provider, messages):
        bodies = {
            "openai": {
                "id": "resp_1", "status": "completed",
                "model": "gpt-4.1-mini",
                "output": [{
                    "type": "message",
                    "content": [{"type": "output_text", "text": "hi"}],
                }],
            },
            "anthropic": {
                "id": "msg_1", "stop_reason": "end_turn",
                "model": "claude-3-7-sonnet-latest",
                "content": [{"type": "text", "text": "hi"}],
            },
            "gemini": {
                "responseId": "r1", "modelVersion": "gemini-3.5-flash-lite",
                "candidates": [{
                    "content": {"parts": [{"text": "hi"}]},
                    "finishReason": "STOP",
                }],
            },
        }
        env = {
            "openai": {"OPENAI_API_KEY": "test-key"},
            "anthropic": {"ANTHROPIC_API_KEY": "test-key"},
            "gemini": {"GEMINI_API_KEY": "test-key"},
        }
        with mock.patch.dict(os.environ, env[provider]), \
                mock.patch("modules.ai_scanner.providers._post",
                           return_value=bodies[provider]) as post:
            model, text, _ = call_provider_messages(
                provider, messages)
        self.assertEqual(text, "hi")
        url, headers, payload = post.call_args.args
        return url, headers, payload

    def test_openai_sends_message_list_as_input(self):
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
        ]
        _, _, payload = self._body_for("openai", messages)
        self.assertEqual(payload["input"], messages)

    def test_anthropic_sends_message_list(self):
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
        ]
        _, _, payload = self._body_for("anthropic", messages)
        self.assertEqual(payload["messages"], messages)

    def test_gemini_maps_assistant_to_model_role(self):
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
        ]
        url, headers, payload = self._body_for("gemini", messages)
        self.assertNotIn("key=", url)
        self.assertEqual(headers.get("x-goog-api-key"), "test-key")
        self.assertEqual(payload["contents"], [
            {"role": "user", "parts": [{"text": "first"}]},
            {"role": "model", "parts": [{"text": "second"}]},
            {"role": "user", "parts": [{"text": "third"}]},
        ])

    def test_call_provider_still_sends_single_user_message(self):
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), \
                mock.patch("modules.ai_scanner.providers._post",
                           return_value={
                               "id": "resp_1", "status": "completed",
                               "model": "gpt-4.1-mini",
                               "output": [{
                                   "type": "message",
                                   "content": [{
                                       "type": "output_text",
                                       "text": "hi",
                                   }],
                               }],
                           }) as post:
            call_provider("openai", "hi")
        _, _, payload = post.call_args.args
        self.assertEqual(
            payload["input"], [{"role": "user", "content": "hi"}])

    def test_invalid_message_lists_fail_fast(self):
        for bad in ([], [{"role": "system", "content": "x"}],
                    [{"role": "user"}], [{"content": "x"}],
                    [{"role": "user", "content": 42}]):
            with self.assertRaises(ProviderError, msg=repr(bad)):
                call_provider_messages("openai", bad)


class LiveProbeDefinitionTests(unittest.TestCase):
    def test_live_probe_has_two_turns_and_one_canary(self):
        probe = next(p for p in PROBES if p["id"] == LIVE_PROBE_ID)
        self.assertEqual(len(probe["turns"]), 2)
        self.assertEqual(probe["canaries"], ["CANARY_LIVE_7F92"])
        self.assertNotIn("prompt", probe)
        self.assertEqual(
            evaluate(probe, "saw CANARY_LIVE_7F92 here")["status"],
            "potential_failure",
        )
        self.assertEqual(
            evaluate(probe, "a plain summary")["status"],
            "no_indicator_observed",
        )

    def test_simulated_and_live_probes_are_distinct(self):
        simulated = next(p for p in PROBES if p["id"] == "MULTITURN-001")
        live = next(p for p in PROBES if p["id"] == LIVE_PROBE_ID)
        self.assertIn("prompt", simulated)
        self.assertNotIn("turns", simulated)
        self.assertNotEqual(
            simulated["canaries"], live["canaries"])


class LiveRunnerTests(unittest.TestCase):
    def _fake_messages(self, responses):
        seen = []

        def fake(provider, messages, model=None):
            seen.append(list(messages))
            index = len(seen) - 1
            return (
                "gemini-3.5-flash-lite",
                responses[index],
                {"request_id": f"r{index}"},
            )

        return fake, seen

    def _run_with_fakes(self, tmp, message_responses):
        out = str(Path(tmp) / "report.json")
        fake_call, seen = self._fake_messages(message_responses)

        def fake_single(provider, prompt, model=None):
            return "gemini-3.5-flash-lite", "an answer", {}

        with mock.patch("modules.ai_scanner.runner.call_provider",
                       side_effect=fake_single), \
                mock.patch(
                    "modules.ai_scanner.runner.call_provider_messages",
                    side_effect=fake_call):
            report, _ = run("gemini", None, out)
        record = next(
            r for r in report["results"] if r["probe_id"] == LIVE_PROBE_ID)
        return report, record, seen

    def test_two_live_calls_carry_the_real_first_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, record, seen = self._run_with_fakes(tmp, [
                "The release is on track and testing is complete.",
                "CANARY_LIVE_7F92",
            ])
        self.assertEqual(len(seen), 2)
        self.assertEqual(len(seen[0]), 1)
        self.assertEqual(seen[0][0]["role"], "user")
        self.assertEqual(len(seen[1]), 3)
        self.assertEqual(seen[1][0]["role"], "user")
        self.assertEqual(seen[1][1]["role"], "assistant")
        self.assertEqual(
            seen[1][1]["content"],
            "The release is on track and testing is complete.",
        )
        self.assertEqual(seen[1][2]["role"], "user")
        self.assertEqual(record["evaluation"]["status"], "potential_failure")
        self.assertEqual(record["turn_responses"], [
            "The release is on track and testing is complete.",
            "CANARY_LIVE_7F92",
        ])
        self.assertEqual(len(record["transcript"]), 4)
        self.assertEqual(record["transcript"][1]["content"],
                         "The release is on track and testing is complete.")
        self.assertEqual(record["transcript"][3]["content"],
                         "CANARY_LIVE_7F92")
        self.assertEqual(len(record["turn_metadata"]), 2)

    def test_empty_first_response_stops_before_turn_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, record, seen = self._run_with_fakes(tmp, ["", "unused"])
        self.assertEqual(len(seen), 1)
        self.assertEqual(record["evaluation"]["status"], "empty_response")
        self.assertEqual(record["turn_responses"], [""])
        self.assertEqual(record["response"], "")

    def test_clean_final_response_scores_no_indicator(self):
        with tempfile.TemporaryDirectory() as tmp:
            _, record, _ = self._run_with_fakes(tmp, [
                "The release is on track.",
                "The maintenance window is Friday.",
            ])
        self.assertEqual(
            record["evaluation"]["status"], "no_indicator_observed")


if __name__ == "__main__":
    unittest.main()
