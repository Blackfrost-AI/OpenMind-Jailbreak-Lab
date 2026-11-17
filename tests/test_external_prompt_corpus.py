"""Integrity checks for the independently authored external-pattern test corpus."""
import json
import unittest
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[1] / "data" / "external_prompt_patterns_v1.jsonl"

class ExternalPromptCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_corpus_has_unique_ids_and_expected_size(self):
        ids = [row["id"] for row in self.rows]
        self.assertEqual(len(self.rows), 15)
        self.assertEqual(len(ids), len(set(ids)))

    def test_adversarial_rows_use_synthetic_canaries(self):
        adversarial = [row for row in self.rows if not row["control"]]
        self.assertEqual(len(adversarial), 12)
        for row in adversarial:
            with self.subTest(case=row["id"]):
                self.assertTrue(row["canary"].startswith("CANARY-EXT-"))
                self.assertEqual(row["expected_signal"], "must_not_emit_canary")
                self.assertIn("untrusted", row["prompt"].casefold())

    def test_controls_have_no_canary(self):
        controls = [row for row in self.rows if row["control"]]
        self.assertEqual(len(controls), 3)
        self.assertTrue(all("canary" not in row for row in controls))

    def test_provenance_and_original_adaptation_are_recorded(self):
        for row in self.rows:
            self.assertEqual(row["source_project"], "togg53192-cmd/jailbreaks")
            self.assertEqual(row["source_reference"], "https://github.com/togg53192-cmd/jailbreaks")
            self.assertEqual(row["adaptation"], "independently_authored_synthetic_test")

if __name__ == "__main__":
    unittest.main()
