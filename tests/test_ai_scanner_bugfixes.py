import io
import json
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

from modules.ai_scanner import __version__, cli
from modules.ai_scanner.providers import ProviderError, _post, call_provider
from modules.ai_scanner.runner import run
from src.validate import validate

LIVE_PROBE_ID = "MULTITURN-LIVE-001"


def _benchmark_row(**overrides):
    row = {
        "id": "OM-001",
        "family": "test family",
        "split": "adversarial",
        "risk_level": "low",
        "user_prompt": "do the task",
        "expected_behavior": "does the task",
        "tags": ["test"],
    }
    row.update(overrides)
    return row


def _write_benchmark(tmp, rows):
    path = Path(tmp) / "bench.jsonl"
    path.write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return str(path)


class ValidatorMalformedFieldTests(unittest.TestCase):
    def test_non_string_split_and_risk_level_do_not_crash(self):
        bad_values = (["adversarial"], {"split": "adversarial"}, 42, None)
        for bad in bad_values:
            for field in ("split", "risk_level"):
                with tempfile.TemporaryDirectory() as tmp:
                    path = _write_benchmark(tmp, [
                        _benchmark_row(**{field: bad}),
                        _benchmark_row(id="OM-002", split="benign"),
                    ])
                    rows, errors = validate(path)
                self.assertTrue(
                    any(f"invalid {field}" in e for e in errors),
                    f"{field}={bad!r} produced no invalid-{field} error: {errors}",
                )

    def test_valid_rows_still_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_benchmark(tmp, [
                _benchmark_row(),
                _benchmark_row(id="OM-002", split="benign"),
            ])
            _, errors = validate(path)
        self.assertEqual(errors, [])


class VersionConsistencyTests(unittest.TestCase):
    def test_report_version_matches_package_version(self):
        def fake_call(provider, prompt, model=None):
            return "gemini-3.5-flash-lite", "an answer", {}

        def fake_call_messages(provider, messages, model=None):
            return "gemini-3.5-flash-lite", "an answer", {}

        with tempfile.TemporaryDirectory() as tmp:
            out = str(Path(tmp) / "report.json")
            with mock.patch("modules.ai_scanner.runner.call_provider",
                           side_effect=fake_call), \
                    mock.patch(
                        "modules.ai_scanner.runner.call_provider_messages",
                        side_effect=fake_call_messages):
                report, _ = run("gemini", None, out)
        self.assertEqual(report["scanner_version"], __version__)
        self.assertTrue(__version__)


class MultiturnPartialPreservationTests(unittest.TestCase):
    def _run_with_message_fake(self, tmp, fake_messages):
        out = str(Path(tmp) / "report.json")

        def fake_single(provider, prompt, model=None):
            return "gemini-3.5-flash-lite", "an answer", {}

        with mock.patch("modules.ai_scanner.runner.call_provider",
                       side_effect=fake_single), \
                mock.patch(
                    "modules.ai_scanner.runner.call_provider_messages",
                    side_effect=fake_messages):
            report, _ = run("gemini", None, out)
        return next(
            r for r in report["results"] if r["probe_id"] == LIVE_PROBE_ID)

    def test_failed_second_turn_preserves_first_turn(self):
        def fake_messages(provider, messages, model=None):
            if len(messages) == 1:
                return ("gemini-3.5-flash-lite",
                        "The release is on track.", {"request_id": "r1"})
            raise ProviderError("HTTP 429: slow down")

        with tempfile.TemporaryDirectory() as tmp:
            record = self._run_with_message_fake(tmp, fake_messages)
        self.assertEqual(record["evaluation"]["status"], "partial_run")
        self.assertEqual(record["turn_responses"],
                         ["The release is on track."])
        self.assertEqual(record["turn_metadata"],
                         [{"request_id": "r1"}])
        self.assertEqual(record["turn_errors"][0], None)
        self.assertIn("429", record["turn_errors"][1])
        self.assertIn("429", record["error"])
        self.assertIsNone(record["response"])
        self.assertEqual(len(record["transcript"]), 3)
        self.assertEqual(record["transcript"][1]["content"],
                         "The release is on track.")
        self.assertEqual(record["metadata"], {"request_id": "r1"})

    def test_failed_first_turn_is_plain_not_run(self):
        def fake_messages(provider, messages, model=None):
            raise ProviderError("HTTP 500: boom")

        with tempfile.TemporaryDirectory() as tmp:
            record = self._run_with_message_fake(tmp, fake_messages)
        self.assertEqual(record["evaluation"]["status"], "not_run")
        self.assertEqual(record["turn_responses"], [])
        self.assertEqual(record["turn_errors"], ["HTTP 500: boom"])
        self.assertEqual(len(record["transcript"]), 1)
        self.assertEqual(record["transcript"][0]["role"], "user")


class MalformedProviderBodyTests(unittest.TestCase):
    def _fake_urlopen(self, payload):
        def fake(request, timeout=60):
            class FakeResponse:
                def read(self):
                    return json.dumps(payload).encode("utf-8")

                def __enter__(self):
                    return self

                def __exit__(self, *exc):
                    return False

            return FakeResponse()

        return fake

    def test_empty_object_body_yields_empty_text(self):
        for provider, env in (
            ("openai", {"OPENAI_API_KEY": "k"}),
            ("anthropic", {"ANTHROPIC_API_KEY": "k"}),
            ("gemini", {"GEMINI_API_KEY": "k"}),
        ):
            with mock.patch.dict(os.environ, env), \
                    mock.patch("urllib.request.urlopen",
                               side_effect=self._fake_urlopen({})):
                _, text, metadata = call_provider(provider, "hi")
            self.assertEqual(text, "")
            self.assertIn("latency_seconds", metadata)

    def test_non_object_json_body_raises_provider_error(self):
        for payload in (["not", "an", "object"], "a string", 42):
            with mock.patch("urllib.request.urlopen",
                           side_effect=self._fake_urlopen(payload)):
                with self.assertRaises(ProviderError):
                    _post("https://example.invalid/", {}, {})

    def test_5xx_retry_exhaustion(self):
        def fake_urlopen(request, timeout=60):
            raise urllib.error.HTTPError(
                "https://example.invalid/", 500, "err", {},
                io.BytesIO(b"boom"),
            )

        with mock.patch("urllib.request.urlopen",
                        side_effect=fake_urlopen) as urlopen, \
                mock.patch("time.sleep"):
            with self.assertRaises(ProviderError) as ctx:
                _post("https://example.invalid/", {}, {})
        self.assertEqual(urlopen.call_count, 3)
        self.assertIn("500", str(ctx.exception))


class ComparisonDuplicateColumnTests(unittest.TestCase):
    def _report(self, provider, model, statuses):
        return {
            "provider": provider,
            "model": model,
            "results": [
                {"probe_id": pid, "evaluation": {"status": st}, "error": None}
                for pid, st in statuses
            ],
        }

    def test_three_identical_provider_model_reports_get_unique_columns(self):
        statuses = [
            ("BOUNDARY-001", "no_indicator_observed"),
            ("INJECTION-001", "potential_failure"),
            ("BOUNDARY-001", "manual_review"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for i, (_, st) in enumerate(statuses):
                p = Path(tmp) / f"run{i}.json"
                p.write_text(json.dumps(self._report(
                    "gemini", "gemini-3.5-flash-lite",
                    [("BOUNDARY-001", st)])), encoding="utf-8")
                paths.append(str(p))
            out = Path(tmp) / "comparison.json"
            code = cli.main(["compare", *paths, "--output", str(out)])
            self.assertEqual(code, 0)
            data = json.loads(out.read_text(encoding="utf-8"))
        columns = [p["column"] for p in data["providers"]]
        self.assertEqual(len(columns), 3)
        self.assertEqual(len(set(columns)), 3)
        self.assertEqual(columns[0], "gemini")
        self.assertEqual(columns[1], "gemini/gemini-3.5-flash-lite")
        self.assertEqual(columns[2], "gemini/gemini-3.5-flash-lite#2")
        seen = {data["probes"]["BOUNDARY-001"][c]["status"]
                for c in columns}
        self.assertEqual(
            seen,
            {"no_indicator_observed", "potential_failure", "manual_review"},
        )


if __name__ == "__main__":
    unittest.main()
