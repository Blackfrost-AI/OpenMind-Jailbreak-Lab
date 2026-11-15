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


class Jb002CaseTests(unittest.TestCase):
    def test_case_ids_unique(self):
        ids = [c["case_id"] for c in load_cases()]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids), 3)

    def test_cases_have_required_fields(self):
        for case in load_cases():
            for key in ("case_id", "test_type", "title", "user_task",
                        "document", "expected", "marker"):
                self.assertTrue(case[key], f"missing {key}")

    def test_markers_are_distinct_harmless_tokens(self):
        cases = load_cases()
        markers = {c["marker"] for c in cases}
        self.assertEqual(len(markers), len(cases))
        for marker in markers:
            self.assertRegex(marker, r"^[A-Z_]+$")
            self.assertNotIn(" ", marker)

    def test_each_marker_appears_in_its_own_document(self):
        for case in load_cases():
            self.assertIn(case["marker"], case["document"])

    def test_list_shows_all_cases(self):
        out = io.StringIO()
        with redirect_stdout(out):
            cli.list_cases()
        text = out.getvalue()
        for case in load_cases():
            self.assertIn(case["case_id"], text)

    def test_prompt_shows_task_document_and_expected(self):
        out = io.StringIO()
        with redirect_stdout(out):
            cli.show_prompt("JB002-01")
        text = out.getvalue()
        self.assertIn("USER TASK", text)
        self.assertIn("DOCUMENT", text)
        self.assertIn("EXPECTED BEHAVIOR", text)

    def test_unknown_prompt_rejected(self):
        with self.assertRaises(SystemExit):
            cli.show_prompt("JB002-99")

    def test_record_writes_one_observation_and_infers_nothing(self):
        answers = iter([
            "JB002-01",              # Case ID
            "google",                # Provider
            "gemini-3.5-flash-lite",  # Exact model/version
            "My own account",        # Authorized scope
            "transcript.txt",        # Transcript reference
            "A two-sentence summary.",  # Exact model output
            "1",                     # Outcome: held_boundary
            "1",                     # Evidence: raw_transcript_saved
            "1",                     # Reproduction count
            "",                      # Observed date (default today)
        ])
        with tempfile.TemporaryDirectory() as tmp:
            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                out = io.StringIO()
                with redirect_stdout(out), mock.patch(
                        "builtins.input", side_effect=lambda *a: next(answers)):
                    cli.record()
                target = Path(tmp) / "records" / "observations.jsonl"
                self.assertTrue(target.exists())
                rows = [json.loads(line) for line in
                        target.read_text(encoding="utf-8").splitlines() if line.strip()]
                self.assertEqual(len(rows), 1)
                row = rows[0]
                self.assertEqual(row["case_id"], "JB002-01")
                self.assertEqual(row["provider"], "google")
                self.assertEqual(row["observed_outcome"], "held_boundary")
                self.assertEqual(row["evidence_status"], "raw_transcript_saved")
                self.assertEqual(row["reproduction_count"], 1)
                self.assertIn("No result was inferred", out.getvalue())
            finally:
                os.chdir(old_cwd)


if __name__ == "__main__":
    unittest.main()
