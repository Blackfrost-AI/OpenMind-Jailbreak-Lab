import json, tempfile, unittest
from pathlib import Path
from src.validate import validate

class ValidationTests(unittest.TestCase):
    def test_shipped_dataset(self):
        rows, errors = validate("data/benchmark_v0.3.jsonl")
        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 30)
    def test_duplicate_id_rejected(self):
        row = {"id":"OM-001","family":"x","split":"adversarial","risk_level":"low","user_prompt":"x","expected_behavior":"y","tags":["z"],"synthetic_secret":None}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.jsonl"; p.write_text(json.dumps(row)+"\n"+json.dumps(row)+"\n")
            _, errors=validate(p)
            self.assertTrue(any("duplicate id" in e for e in errors))
    def test_benign_secret_rejected(self):
        row = {"id":"OM-002","family":"x","split":"benign","risk_level":"low","user_prompt":"x","expected_behavior":"y","tags":["z"],"synthetic_secret":"oops"}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.jsonl"; p.write_text(json.dumps(row)+"\n")
            _, errors=validate(p)
            self.assertTrue(any("benign control" in e for e in errors))

if __name__ == "__main__": unittest.main()
