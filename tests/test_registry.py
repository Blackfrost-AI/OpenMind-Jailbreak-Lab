import json, tempfile, unittest
from pathlib import Path
from modules.guardrail_lab.registry import add_finding, load_registry, export_markdown, save_candidate_records

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
    def test_confirm_requires_two_successful_repeats(self):
        row={**BASE,"status":"confirmed","assessment":"potential_guardrail_failure","review_notes":"Reviewed","repeat_runs":3,"repeat_successes":1}
        with self.assertRaisesRegex(ValueError,"repeat_runs"): add_finding(Path("unused"),row,True)
    def test_non_object_registry_entry_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.jsonl"; p.write_text('[]\n')
            with self.assertRaisesRegex(ValueError,"JSON object"): load_registry(p)
    def test_tampering_detected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.jsonl"; add_finding(p,BASE); row=json.loads(p.read_text()); row["summary"]="tampered"; p.write_text(json.dumps(row)+"\n")
            with self.assertRaisesRegex(ValueError,"integrity check"): load_registry(p)
    def test_candidate_signals_are_saved_unverified_and_idempotently(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"registry.jsonl"
            report={"provider":"mock","model":"mock-v1","generated_at":"2026-11-16T12:00:00Z",
                    "results":[{"case_id":"GL-001","category":"quoted_injection",
                                "assessment":"potential_guardrail_failure","started_at":"2026-11-16T12:00:00Z",
                                "evidence_sha256":"a"*64},
                               {"case_id":"GL-002","assessment":"ambiguous_canary_mention"}]}
            saved=save_candidate_records(report,"reports/run.json",p)
            self.assertEqual(len(saved),1)
            self.assertEqual(saved[0]["status"],"unverified")
            self.assertEqual(saved[0]["case_id"],"GL-001")
            self.assertEqual(save_candidate_records(report,"reports/run.json",p),[])
            self.assertEqual(len(load_registry(p)),1)

    def test_markdown_export(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"r.jsonl"; add_finding(p,BASE); out=Path(d)/"out.md"; export_markdown(load_registry(p),out)
            self.assertIn("OM-FND-0001",out.read_text())

if __name__ == "__main__": unittest.main()
