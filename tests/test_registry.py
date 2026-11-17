import json, tempfile, unittest
from pathlib import Path
from modules.guardrail_lab.registry import add_finding, load_registry, export_markdown

BASE = {"finding_id":"OM-FND-0001","title":"Synthetic canary disclosure","provider":"test-provider","model":"test-model","category":"indirect_prompt_injection","status":"unverified","discovered_at":"2026-11-16T12:00:00Z","evidence_ref":"runs/test.json","summary":"Synthetic marker observed; requires review."}

class RegistryTests(unittest.TestCase):
    def test_add_load_and_hash(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"registry.jsonl"; row=add_finding(p,BASE); loaded=load_registry(p)
            self.assertEqual(len(loaded),1); self.assertEqual(loaded[0]["record_sha256"],row["record_sha256"])
    def test_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"registry.jsonl"; add_finding(p,BASE)
            with self.assertRaisesRegex(ValueError,"already exists"): add_finding(p,BASE)
    def test_confirm_requires_explicit_flag_and_repeats(self):
        row={**BASE,"status":"confirmed","assessment":"potential_guardrail_failure","review_notes":"Human reviewed","repeat_runs":3,"repeat_successes":2}
        with self.assertRaisesRegex(ValueError,"confirm-review"): add_finding(Path("unused"),row)
        with tempfile.TemporaryDirectory() as d: self.assertEqual(add_finding(Path(d)/"r.jsonl",row,True)["status"],"confirmed")
    def test_confirm_without_repeats_rejected(self):
        row={**BASE,"status":"confirmed","assessment":"potential_guardrail_failure","review_notes":"Reviewed"}
        with self.assertRaisesRegex(ValueError,"repeat_runs"): add_finding(Path("unused"),row,True)
    def test_tampering_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.jsonl"; add_finding(p,BASE); row=json.loads(p.read_text()); row["summary"]="tampered"; p.write_text(json.dumps(row)+"\n")
            with self.assertRaisesRegex(ValueError,"integrity check"): load_registry(p)
    def test_markdown_export(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.jsonl"; add_finding(p,BASE); out=Path(d)/"out.md"; export_markdown(load_registry(p),out)
            self.assertIn("OM-FND-0001",out.read_text())

if __name__ == "__main__": unittest.main()
