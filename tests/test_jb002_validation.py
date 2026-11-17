import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from modules.jb002 import cli

CASES_PATH = Path("modules/jb002/cases.json")


def load_cases():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def valid_record(**overrides):
    record = {
        "case_id": "JB002-01",
        "provider": "google",
        "model": "gemini-3.5-flash-lite",
        "observed_at": "2026-11-15",
        "test_type": "embedded_prompt_injection",
        "authorized_scope": "My own account",
        "input_transcript": "transcript.txt",
        "model_output": "A two-sentence summary.",
        "expected_boundary": "A two-sentence summary of the operations note.",
        "observed_outcome": "held_boundary",
        "evidence_status": "raw_transcript_saved",
        "reproduction_count": 1,
    }
    record.update(overrides)
    return record


class Jb002FormattingTests(unittest.TestCase):
    def test_no_literal_backslash_n_in_case_text(self):
        for case in load_cases():
            for field in ("user_task", "document", "expected"):
                self.assertNotIn("\\n", case[field],
                                 f"{case['case_id']} {field} has literal \\n")

    def test_documents_have_real_line_breaks(self):
        for case in load_cases():
            self.assertIn("\n", case["document"],
                          f"{case['case_id']} document has no real line break")

    def test_prompt_renders_real_line_breaks(self):
        out = io.StringIO()
        with redirect_stdout(out):
            cli.show_prompt("JB002-01")
        text = out.getvalue()
        self.assertNotIn("\\n", text)
        self.assertIn("\n\n", text)


class Jb002ValidateRecordTests(unittest.TestCase):
    def test_valid_record_passes(self):
        self.assertEqual(cli.validate_record(valid_record()), [])

    def test_missing_field_rejected(self):
        record = valid_record()
        del record["model"]
        errors = cli.validate_record(record)
        self.assertTrue(any("model" in e for e in errors))

    def test_empty_text_field_rejected(self):
        errors = cli.validate_record(valid_record(model="   "))
        self.assertTrue(any("model" in e for e in errors))

    def test_bad_outcome_rejected(self):
        errors = cli.validate_record(valid_record(observed_outcome="leaked"))
        self.assertTrue(any("observed_outcome" in e for e in errors))

    def test_bad_evidence_rejected(self):
        errors = cli.validate_record(valid_record(evidence_status="trust_me"))
        self.assertTrue(any("evidence_status" in e for e in errors))

    def test_bad_provider_rejected(self):
        errors = cli.validate_record(valid_record(provider="openrouter"))
        self.assertTrue(any("provider" in e for e in errors))

    def test_bad_case_id_rejected(self):
        errors = cli.validate_record(valid_record(case_id="JB002-99"))
        self.assertTrue(any("case_id" in e for e in errors))

    def test_impossible_dates_rejected(self):
        for bad in ("2026-02-30", "2026-13-01", "2026-00-10", "2026-11-31"):
            errors = cli.validate_record(valid_record(observed_at=bad))
            self.assertTrue(any("observed_at" in e for e in errors), bad)

    def test_wrong_date_shapes_rejected(self):
        for bad in ("15/11/2026", "yesterday", "2026-11-5", "20261115"):
            errors = cli.validate_record(valid_record(observed_at=bad))
            self.assertTrue(any("observed_at" in e for e in errors), bad)

    def test_valid_dates_accepted(self):
        for good in ("2026-11-15", "2024-02-29"):
            self.assertEqual(cli.validate_record(valid_record(observed_at=good)), [], good)

    def test_count_below_one_rejected(self):
        errors = cli.validate_record(valid_record(reproduction_count=0))
        self.assertTrue(any("reproduction_count" in e for e in errors))

    def test_non_integer_count_rejected(self):
        for bad in ("2", 1.5, True):
            errors = cli.validate_record(valid_record(reproduction_count=bad))
            self.assertTrue(any("reproduction_count" in e for e in errors), repr(bad))

    def test_unexpected_field_rejected(self):
        record = valid_record(extra="nope")
        errors = cli.validate_record(record)
        self.assertTrue(any("unexpected field" in e for e in errors))

    def test_non_object_rejected(self):
        self.assertTrue(cli.validate_record(["not", "a", "record"]))

    def test_transcript_field_accepted(self):
        record = valid_record(transcript="full transcript text")
        self.assertEqual(cli.validate_record(record), [])

    def test_transcript_reference_field_accepted(self):
        record = valid_record(transcript_reference="kept in my notes")
        self.assertEqual(cli.validate_record(record), [])

    def test_both_transcript_fields_rejected(self):
        record = valid_record(transcript="x", transcript_reference="y")
        errors = cli.validate_record(record)
        self.assertTrue(any("not both" in e for e in errors))

    def test_empty_transcript_rejected(self):
        errors = cli.validate_record(valid_record(transcript=""))
        self.assertTrue(any("transcript" in e for e in errors))


class Jb002RecordRepromptTests(unittest.TestCase):
    def _run_record(self, answers):
        answers = iter(answers)
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                out = io.StringIO()
                with redirect_stdout(out), mock.patch(
                        "builtins.input", side_effect=lambda *a: next(answers)):
                    cli.record()
                target = Path(tmp) / "records" / "observations.jsonl"
                rows = [json.loads(line) for line in
                        target.read_text(encoding="utf-8").splitlines() if line.strip()]
                return rows, out.getvalue()
            finally:
                os.chdir(old_cwd)

    def _base_answers(self):
        return [
            "JB002-01",              # Case ID
            "google",                # Provider
            "gemini-3.5-flash-lite",  # Exact model/version
            "My own account",        # Authorized scope
            "kept in my notes",      # Transcript reference (not a file path)
            "A two-sentence summary.",  # Exact model output
            "",                      # End multi-line output
        ]

    def test_record_reprompts_on_bad_date(self):
        answers = self._base_answers() + [
            "1",            # Outcome: held_boundary
            "1",            # Evidence: raw_transcript_saved
            "1",            # Reproduction count
            "2026-02-30",   # Invalid date (no such day)
            "15/11/2026",   # Wrong shape
            "2026-11-15",   # Valid date
        ]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["observed_at"], "2026-11-15")
        self.assertIn("Invalid date", output)

    def test_record_reprompts_on_bad_outcome(self):
        answers = self._base_answers() + [
            "9",            # Invalid outcome
            "1",            # Outcome: held_boundary
            "1",            # Evidence: raw_transcript_saved
            "1",            # Reproduction count
            "",             # Observed date (default today)
        ]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["observed_outcome"], "held_boundary")
        self.assertIn("Invalid choice", output)

    def test_record_reprompts_on_bad_count(self):
        answers = self._base_answers() + [
            "1",            # Outcome: held_boundary
            "1",            # Evidence: raw_transcript_saved
            "0",            # Invalid count
            "two",          # Invalid count
            "2",            # Valid count
            "",             # Observed date (default today)
        ]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["reproduction_count"], 2)
        self.assertIn("must be an integer >= 1", output)


class Jb002ValidateFileTests(unittest.TestCase):
    def _write_temp(self, lines):
        fd, name = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        self.addCleanup(os.unlink, name)
        return name

    def test_valid_file_passes(self):
        path = self._write_temp([json.dumps(valid_record())])
        checked, errors = cli.validate_file(path)
        self.assertEqual((checked, errors), (1, []))

    def test_bad_rows_reported_with_line_numbers(self):
        path = self._write_temp([
            json.dumps(valid_record()),
            json.dumps(valid_record(observed_at="2026-02-30")),
            "{not json",
            json.dumps(valid_record(observed_outcome="leaked")),
        ])
        checked, errors = cli.validate_file(path)
        self.assertEqual(checked, 3)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("line 2" in e for e in errors))
        self.assertTrue(any("line 3" in e for e in errors))
        self.assertTrue(any("line 4" in e for e in errors))

    def test_validate_command_exits_zero_on_clean_file(self):
        path = self._write_temp([json.dumps(valid_record())])
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(["validate", path])
        self.assertIn("all valid", out.getvalue())

    def test_validate_command_exits_one_on_bad_file(self):
        path = self._write_temp([json.dumps(valid_record(observed_at="yesterday"))])
        with self.assertRaises(SystemExit) as ctx:
            cli.main(["validate", path])
        self.assertEqual(ctx.exception.code, 1)

    def test_validate_command_ok_with_missing_file(self):
        out = io.StringIO()
        with redirect_stdout(out):
            cli.main(["validate", "does-not-exist.jsonl"])
        self.assertIn("nothing to validate", out.getvalue())


class Jb002FreeTextRepromptTests(unittest.TestCase):
    def test_url_is_treated_as_a_transcript_reference(self):
        self.assertFalse(cli.looks_like_path("https://example.org/research/transcript.txt"))
        self.assertTrue(cli.looks_like_path("notes/transcript.txt"))

    def _run_record(self, answers, files=None):
        answers = iter(answers)
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                for name, content in (files or {}).items():
                    Path(tmp, name).write_text(content, encoding="utf-8")
                out = io.StringIO()
                with redirect_stdout(out), mock.patch(
                        "builtins.input", side_effect=lambda *a: next(answers)):
                    cli.record()
                target = Path(tmp) / "records" / "observations.jsonl"
                rows = [json.loads(line) for line in
                        target.read_text(encoding="utf-8").splitlines() if line.strip()]
                return rows, out.getvalue()
            finally:
                os.chdir(old_cwd)

    def _answers(self, model="gemini-3.5-flash-lite", scope="My own account",
                 transcript="kept in my notes", output=("A two-sentence summary.",)):
        answers = ["JB002-01", "google", model, scope, transcript]
        answers.extend(output)
        answers.append("")  # End multi-line output
        answers.extend(["1", "1", "1", ""])  # Outcome, evidence, count, date
        return answers

    def test_record_reprompts_on_empty_model(self):
        answers = ["JB002-01", "google",
                   "", "gemini-3.5-flash-lite",  # Blank model: reprompted
                   "My own account", "kept in my notes",
                   "A two-sentence summary.", "",
                   "1", "1", "1", ""]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["model"], "gemini-3.5-flash-lite")
        self.assertIn("required", output)

    def test_record_reprompts_on_empty_provider(self):
        answers = ["JB002-01",
                   "", "google",  # Blank provider: reprompted, not a crash
                   "gemini-3.5-flash-lite",
                   "My own account", "kept in my notes",
                   "A two-sentence summary.", "",
                   "1", "1", "1", ""]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["provider"], "google")
        self.assertIn("required", output)

    def test_record_reprompts_on_empty_scope(self):
        answers = ["JB002-01", "google", "gemini-3.5-flash-lite",
                   "", "My own account",  # Blank scope: reprompted
                   "kept in my notes",
                   "A two-sentence summary.", "",
                   "1", "1", "1", ""]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["authorized_scope"], "My own account")
        self.assertIn("required", output)

    def test_record_reprompts_on_empty_transcript(self):
        answers = ["JB002-01", "google", "gemini-3.5-flash-lite",
                   "My own account",
                   "", "kept in my notes",  # Blank transcript: reprompted
                   "A two-sentence summary.", "",
                   "1", "1", "1", ""]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transcript_reference"], "kept in my notes")
        self.assertIn("required", output)

    def test_record_reprompts_on_empty_output(self):
        answers = ["JB002-01", "google", "gemini-3.5-flash-lite",
                   "My own account", "kept in my notes",
                   "",  # Blank output: reprompted
                   "A two-sentence summary.", "",
                   "1", "1", "1", ""]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["model_output"], "A two-sentence summary.")
        self.assertIn("required", output)

    def test_record_embeds_transcript_file(self):
        contents = "User message here.\nModel reply here.\n"
        rows, _ = self._run_record(
            self._answers(transcript="transcript.txt"),
            files={"transcript.txt": contents})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transcript"], contents)
        self.assertNotIn("transcript_reference", rows[0])
        self.assertNotIn("Transcript reference", rows[0]["input_transcript"])

    def test_record_accepts_url_transcript_reference(self):
        url = "https://example.org/research/transcript.txt"
        rows, output = self._run_record(self._answers(transcript=url))
        self.assertEqual(rows[0]["transcript_reference"], url)
        self.assertNotIn("No such file", output)

    def test_record_stores_reference_when_not_a_path(self):
        rows, _ = self._run_record(self._answers())
        self.assertEqual(rows[0]["transcript_reference"], "kept in my notes")
        self.assertNotIn("transcript", rows[0])

    def test_record_reprompts_on_missing_path(self):
        answers = ["JB002-01", "google", "gemini-3.5-flash-lite",
                   "My own account",
                   "notes/missing.txt",  # Looks like a path, file absent
                   "kept in my notes",
                   "A two-sentence summary.", "",
                   "1", "1", "1", ""]
        rows, output = self._run_record(answers)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["transcript_reference"], "kept in my notes")
        self.assertIn("No such file", output)

    def test_record_captures_multiline_output(self):
        rows, _ = self._run_record(
            self._answers(output=("Line one.", "Line two.")))
        self.assertEqual(rows[0]["model_output"], "Line one.\nLine two.")


if __name__ == "__main__":
    unittest.main()
