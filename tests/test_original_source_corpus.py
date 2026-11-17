import json
import tempfile
import unittest
from pathlib import Path

from modules.original_source_corpus.__main__ import load_index, review_template

class OriginalSourceCorpusTests(unittest.TestCase):
    def test_checked_in_inventory_loads_and_is_non_runnable(self):
        records = load_index()
        self.assertGreaterEqual(len(records), 50)
        self.assertTrue(all(item["runnable"] is False for item in records))
        self.assertEqual(len({item["id"] for item in records}), len(records))

    def test_rejects_runnable_raw_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(json.dumps({"id":"X","path":"x","bytes":1,"sha256":"0"*64,"status":"metadata_only","runnable":True}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must remain non-runnable"):
                load_index(path)

    def test_review_template_is_provenance_bound_and_not_approval(self):
        record = {"id":"SRC-001","path":"x.md","sha256":"a"*64}
        result = review_template(record)
        self.assertEqual(result["source_id"], "SRC-001")
        self.assertFalse(result["runnable_approval"])
        self.assertIn("does not add", result["warning"])

if __name__ == "__main__":
    unittest.main()
