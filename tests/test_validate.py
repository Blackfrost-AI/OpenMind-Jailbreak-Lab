import json
import tempfile
import unittest
from pathlib import Path

from src.validate import validate


def case(case_id="OM-001", split="adversarial", **overrides):
    row = {
        "id": case_id,
        "family": "test_family",
        "split": split,
        "risk_level": "low",
        "user_prompt": "Do a harmless task.",
        "expected_behavior": "Complete the task.",
        "tags": ["unit_test"],
        "synthetic_secret": None,
    }
    row.update(overrides)
    return row


class ValidationTests(unittest.TestCase):
    def run_rows(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.jsonl"
            path.write_text(
                "".join(json.dumps(row) + "\n" for row in rows),
                encoding="utf-8",
            )
            return validate(path)

    def test_shipped_v04_dataset(self):
        rows, errors = validate("data/benchmark_v0.4.jsonl")
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 44)
        self.assertEqual(sum(row["split"] == "adversarial" for row in rows), 23)
        self.assertEqual(sum(row["split"] == "benign" for row in rows), 21)

    def test_duplicate_id_rejected(self):
        _, errors = self.run_rows([
            case(case_id="OM-001"),
            case(case_id="OM-001", split="benign"),
        ])
        self.assertTrue(any("duplicate id" in error for error in errors))

    def test_benign_secret_rejected(self):
        _, errors = self.run_rows([
            case(split="benign", synthetic_secret="not-allowed"),
            case(case_id="OM-002", split="adversarial"),
        ])
        self.assertTrue(any("benign control" in error for error in errors))

    def test_non_string_secret_rejected(self):
        _, errors = self.run_rows([
            case(synthetic_secret=42),
            case(case_id="OM-002", split="benign"),
        ])
        self.assertTrue(any("synthetic_secret must be a string or null" in error for error in errors))

    def test_blank_tag_rejected(self):
        _, errors = self.run_rows([
            case(tags=["   "]),
            case(case_id="OM-002", split="benign"),
        ])
        self.assertTrue(any("tags must be" in error for error in errors))

    def test_short_family_rejected(self):
        _, errors = self.run_rows([
            case(family="ab"),
            case(case_id="OM-002", split="benign"),
        ])
        self.assertTrue(any("family must contain" in error for error in errors))

    def test_empty_dataset_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.jsonl"
            path.write_text("", encoding="utf-8")
            _, errors = validate(path)
        self.assertTrue(any("at least one valid record" in error for error in errors))

    def test_both_splits_required(self):
        _, errors = self.run_rows([case()])
        self.assertTrue(any("both adversarial and benign" in error for error in errors))

    def test_invalid_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.jsonl"
            path.write_text('{"id":\n', encoding="utf-8")
            _, errors = validate(path)
        self.assertTrue(any("invalid JSON" in error for error in errors))

    def test_blank_line_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "blank.jsonl"
            path.write_text(json.dumps(case()) + "\n\n" + json.dumps(case(
                case_id="OM-002", split="benign"
            )) + "\n", encoding="utf-8")
            _, errors = validate(path)
        self.assertTrue(any("blank lines are not allowed" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
