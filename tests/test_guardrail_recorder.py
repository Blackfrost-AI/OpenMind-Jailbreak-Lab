import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from openmind.report import load_records, main


class RecorderTests(unittest.TestCase):
    def write_records(self, lines):
        handle = tempfile.NamedTemporaryFile(
            "w", suffix=".jsonl", delete=False, encoding="utf-8")
        handle.write("\n".join(lines))
        if lines:
            handle.write("\n")
        handle.close()
        return handle.name

    def record(self, **overrides):
        row = {
            "case_id": "OM-OBS-0001",
            "provider": "google",
            "model": "gemini-3.5-flash-lite",
            "observed_outcome": "held_boundary",
            "evidence_status": "raw_transcript_saved",
            "test_type": "refusal_consistency",
        }
        row.update(overrides)
        return json.dumps(row)

    def test_loads_valid_records(self):
        path = self.write_records([self.record(), self.record(case_id="OM-OBS-0002")])
        self.assertEqual(len(load_records(path)), 2)

    def test_empty_input_is_allowed(self):
        path = self.write_records([])
        self.assertEqual(load_records(path), [])

    def test_invalid_json_rejected(self):
        path = self.write_records(["{not json"])
        with self.assertRaises(SystemExit):
            load_records(path)

    def test_missing_required_field_rejected(self):
        row = json.loads(self.record())
        del row["provider"]
        path = self.write_records([json.dumps(row)])
        with self.assertRaises(SystemExit):
            load_records(path)

    def test_summary_counts_by_provider_family_and_evidence(self):
        path = self.write_records([
            self.record(),
            self.record(case_id="OM-OBS-0002", observed_outcome="boundary_failure",
                        evidence_status="independently_reproduced"),
        ])
        out = io.StringIO()
        with redirect_stdout(out):
            import sys
            old_argv = sys.argv
            sys.argv = ["report", path]
            try:
                main()
            finally:
                sys.argv = old_argv
        text = out.getvalue()
        self.assertIn("Records: 2", text)
        self.assertIn("google: boundary_failure=1, held_boundary=1", text)
        self.assertIn("refusal_consistency: boundary_failure=1, held_boundary=1", text)
        self.assertIn("independently_reproduced: 1", text)

    def test_shipped_example_is_a_template_only(self):
        path = Path("records/observations.example.jsonl")
        if not path.exists():
            self.skipTest("example observations file is not included")
        rows = load_records(str(path))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["observed_outcome"], "inconclusive")
        self.assertEqual(rows[0]["evidence_status"], "unverified")


if __name__ == "__main__":
    unittest.main()
