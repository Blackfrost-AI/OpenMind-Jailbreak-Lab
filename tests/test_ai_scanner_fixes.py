import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from modules.ai_scanner import __version__, cli
from modules.ai_scanner.probes import PROBES, evaluate
from modules.ai_scanner.providers import ProviderError, _post, call_provider
from modules.ai_scanner.runner import run

NEW_PROBE_IDS = (
    "ENCODING-001",
    "MULTILINGUAL-001",
    "AUTHORITY-001",
    "ROLE-001",
    "MULTITURN-001",
    "MULTITURN-LIVE-001",
)


class FakeResponse:
    """Minimal urlopen response: context manager with a JSON body."""

    def __init__(self, payload):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def http_error(code, body="error", headers=None):
    return urllib.error.HTTPError(
        "https://example.invalid/", code, "err", headers or {},
        io.BytesIO(body.encode("utf-8")),
    )


class GeminiHeaderAuthTests(unittest.TestCase):
    def test_key_goes_in_header_not_url(self):
        body = {
            "responseId": "r1",
            "modelVersion": "gemini-3.5-flash-lite",
            "usageMetadata": {"promptTokenCount": 3},
            "candidates": [{
                "content": {"parts": [{"text": "hi"}]},
                "finishReason": "STOP",
            }],
        }
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}), \
                mock.patch("modules.ai_scanner.providers._post",
                           return_value=body) as post:
            model, text, metadata = call_provider("gemini", "hi")
        url, headers, payload = post.call_args.args
        self.assertNotIn("key=", url)
        self.assertNotIn("test-key", url)
        self.assertEqual(headers.get("x-goog-api-key"), "test-key")
        self.assertEqual(text, "hi")
        self.assertEqual(metadata["request_id"], "r1")
        self.assertEqual(metadata["finish_reason"], "STOP")
        self.assertEqual(metadata["usage"], {"promptTokenCount": 3})
        self.assertIn("latency_seconds", metadata)

    def test_missing_key_still_fails_fast(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderError):
                call_provider("gemini", "hi")


class EmptyResponseTests(unittest.TestCase):
    def test_empty_response_is_not_a_clean_result(self):
        probe = next(p for p in PROBES if p["id"] == "BOUNDARY-001")
        for bad in ("", "   ", None):
            result = evaluate(probe, bad)
            self.assertEqual(result["status"], "empty_response", repr(bad))

    def test_empty_response_without_canaries(self):
        probe = next(p for p in PROBES if p["id"] == "DISCLOSURE-001")
        self.assertEqual(evaluate(probe, "")["status"], "empty_response")

    def test_nonempty_response_still_scored(self):
        probe = next(p for p in PROBES if p["id"] == "BOUNDARY-001")
        self.assertEqual(
            evaluate(probe, "I will summarize the note.")["status"],
            "no_indicator_observed",
        )


class OpenAIParsingTests(unittest.TestCase):
    def test_refusal_text_is_captured(self):
        body = {
            "id": "resp_1",
            "status": "completed",
            "usage": {"input_tokens": 10, "output_tokens": 4},
            "model": "gpt-4.1-mini",
            "output": [{
                "type": "message",
                "content": [
                    {"type": "output_text", "text": "The date is 2026-12-02."},
                    {"type": "refusal", "refusal": "I cannot share that."},
                ],
            }],
        }
        with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}), \
                mock.patch("modules.ai_scanner.providers._post",
                           return_value=body):
            model, text, metadata = call_provider("openai", "hi")
        self.assertIn("The date is 2026-12-02.", text)
        self.assertIn("[refusal] I cannot share that.", text)
        self.assertEqual(metadata["request_id"], "resp_1")
        self.assertEqual(metadata["status"], "completed")
        self.assertEqual(metadata["usage"]["input_tokens"], 10)
        self.assertIn("latency_seconds", metadata)

    def test_anthropic_metadata_captured(self):
        body = {
            "id": "msg_1",
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 5},
            "model": "claude-3-7-sonnet-latest",
            "content": [{"type": "text", "text": "hi"}],
        }
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}), \
                mock.patch("modules.ai_scanner.providers._post",
                           return_value=body):
            model, text, metadata = call_provider("anthropic", "hi")
        self.assertEqual(text, "hi")
        self.assertEqual(metadata["request_id"], "msg_1")
        self.assertEqual(metadata["stop_reason"], "end_turn")


class RetryTests(unittest.TestCase):
    def test_retries_429_then_succeeds(self):
        calls = {"n": 0}

        def fake_urlopen(request, timeout=60):
            calls["n"] += 1
            if calls["n"] < 3:
                raise http_error(429, "slow down")
            return FakeResponse({"ok": True})

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
                mock.patch("time.sleep") as sleep:
            result = _post("https://example.invalid/", {}, {})
        self.assertEqual(result, {"ok": True})
        self.assertEqual(calls["n"], 3)
        self.assertEqual(sleep.call_count, 2)

    def test_retry_after_header_is_honored(self):
        def fake_urlopen(request, timeout=60):
            if fake_urlopen.calls == 0:
                fake_urlopen.calls = 1
                raise http_error(429, "slow down",
                                 headers={"Retry-After": "5"})
            return FakeResponse({"ok": True})
        fake_urlopen.calls = 0

        with mock.patch("urllib.request.urlopen", side_effect=fake_urlopen), \
                mock.patch("time.sleep") as sleep:
            _post("https://example.invalid/", {}, {})
        sleep.assert_called_with(5.0)

    def test_no_retry_on_400(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=http_error(400, "bad request")) as urlopen:
            with self.assertRaises(ProviderError):
                _post("https://example.invalid/", {}, {})
        self.assertEqual(urlopen.call_count, 1)

    def test_429_exhausted_after_three_attempts(self):
        with mock.patch("urllib.request.urlopen",
                        side_effect=http_error(429, "slow down")) as urlopen, \
                mock.patch("time.sleep"):
            with self.assertRaises(ProviderError) as ctx:
                _post("https://example.invalid/", {}, {})
        self.assertEqual(urlopen.call_count, 3)
        self.assertIn("429", str(ctx.exception))


class NewProbeTests(unittest.TestCase):
    def test_eleven_probes_with_unique_ids(self):
        ids = [p["id"] for p in PROBES]
        self.assertEqual(len(ids), 11)
        self.assertEqual(len(ids), len(set(ids)))

    def test_new_probes_each_carry_one_canary(self):
        for probe_id in NEW_PROBE_IDS:
            probe = next(p for p in PROBES if p["id"] == probe_id)
            self.assertEqual(len(probe["canaries"]), 1)
            result = evaluate(probe, f"saw {probe['canaries'][0]} here")
            self.assertEqual(result["status"], "potential_failure")
            clean = evaluate(probe, "a plain answer")
            self.assertEqual(clean["status"], "no_indicator_observed")


class RunnerMetadataTests(unittest.TestCase):
    def test_record_carries_provider_metadata(self):
        def fake_call(provider, prompt, model=None):
            return "gemini-3.5-flash-lite", "an answer", {
                "request_id": "r9", "latency_seconds": 0.5,
            }

        def fake_call_messages(provider, messages, model=None):
            return "gemini-3.5-flash-lite", "an answer", {
                "request_id": "r9", "latency_seconds": 0.5,
            }

        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "report.json")
            with mock.patch("modules.ai_scanner.runner.call_provider",
                           side_effect=fake_call), \
                    mock.patch(
                        "modules.ai_scanner.runner.call_provider_messages",
                        side_effect=fake_call_messages):
                report, _ = run("gemini", None, out)
        self.assertEqual(report["scanner_version"], __version__)
        self.assertEqual(report["schema_version"], "1.2")
        record = report["results"][0]
        self.assertEqual(record["metadata"]["request_id"], "r9")
        self.assertEqual(record["metadata"]["latency_seconds"], 0.5)


class CompareTests(unittest.TestCase):
    def _report(self, provider, model, statuses):
        return {
            "provider": provider,
            "model": model,
            "results": [
                {"probe_id": pid, "evaluation": {"status": st}, "error": None}
                for pid, st in statuses
            ],
        }

    def test_compare_builds_matrix_and_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            p1 = Path(tmp) / "gemini.json"
            p2 = Path(tmp) / "openai.json"
            out = Path(tmp) / "comparison.json"
            p1.write_text(json.dumps(self._report(
                "gemini", "gemini-3.5-flash-lite",
                [("BOUNDARY-001", "no_indicator_observed"),
                 ("INJECTION-001", "potential_failure")])), encoding="utf-8")
            p2.write_text(json.dumps(self._report(
                "openai", "gpt-4.1-mini",
                [("BOUNDARY-001", "no_indicator_observed"),
                 ("INJECTION-001", "no_indicator_observed")])), encoding="utf-8")
            buf = io.StringIO()
            from contextlib import redirect_stdout
            with redirect_stdout(buf):
                code = cli.main(["compare", str(p1), str(p2),
                                 "--output", str(out)])
            self.assertEqual(code, 0)
            text = buf.getvalue()
            self.assertIn("BOUNDARY-001", text)
            self.assertIn("potential_failure", text)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(data["providers"]), 2)
            self.assertEqual(
                data["probes"]["INJECTION-001"]["gemini"]["status"],
                "potential_failure",
            )
            self.assertEqual(
                data["probes"]["INJECTION-001"]["openai"]["status"],
                "no_indicator_observed",
            )


if __name__ == "__main__":
    unittest.main()
