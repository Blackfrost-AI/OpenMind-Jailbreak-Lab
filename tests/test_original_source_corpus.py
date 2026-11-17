import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from modules.original_source_corpus.__main__ import load_index, main, review_template

def _record(**overrides):
    record = {"id": "X", "path": "x.md", "bytes": 1, "sha256": "a" * 64,
              "status": "metadata_only", "runnable": False}
    record.update(overrides)
    return record


class OriginalSourceCorpusTests(unittest.TestCase):
    def test_checked_in_inventory_loads_and_is_non_runnable(self):
        records = load_index()
        self.assertGreaterEqual(len(records), 50)
        self.assertTrue(all(item["runnable"] is False for item in records))
        self.assertEqual(len({item["id"] for item in records}), len(records))

    def test_rejects_runnable_raw_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text(json.dumps(_record(runnable=True)) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must remain non-runnable"):
                load_index(path)

    def test_rejects_malformed_fields(self):
        bad = [
            _record(sha256="xyz"),
            _record(sha256="A" * 64),
            _record(sha256="a" * 63),
            _record(bytes="100"),
            _record(bytes=True),
            _record(bytes=-5),
            _record(id=""),
            _record(id=12),
            _record(path=""),
            _record(status=""),
        ]
        for item in bad:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "bad.jsonl"
                path.write_text(json.dumps(item) + "\n", encoding="utf-8")
                with self.assertRaises(ValueError, msg=f"accepted malformed record: {item}"):
                    load_index(path)

    def test_unknown_id_exits_nonzero(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--id", "SRC-999"])
        self.assertEqual(code, 2)
        self.assertIn("unknown source id", err.getvalue())

    def test_search_with_no_matches_still_succeeds(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(["--search", "no-such-collection-xyz"])
        self.assertEqual(code, 0)
        self.assertIn("0 source record(s)", out.getvalue())

    def test_verify_archive_resolves_manifest_outside_repo_root(self):
        repo_root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "dummy.zip"
            archive.write_bytes(b"not the real archive")
            old_cwd = os.getcwd()
            try:
                os.chdir(tmp)
                out, err = io.StringIO(), io.StringIO()
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = main(["--index", str(repo_root / "data/source_corpus/source_inventory.jsonl"),
                                 "--verify-archive", str(archive)])
            finally:
                os.chdir(old_cwd)
        self.assertEqual(code, 2)
        report = json.loads(out.getvalue())
        self.assertIs(report["matches"], False)

    def test_manifest_counts_placeholder_separately(self):
        repo_root = Path(__file__).resolve().parents[1]
        manifest = json.loads((repo_root / "data/source_corpus/manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["empty_file_count"], 0)
        self.assertEqual(manifest["one_byte_placeholder_count"], 1)

    def test_review_template_is_provenance_bound_and_not_approval(self):
        record = {"id":"SRC-001","path":"x.md","sha256":"a"*64}
        result = review_template(record)
        self.assertEqual(result["source_id"], "SRC-001")
        self.assertFalse(result["runnable_approval"])
        self.assertIn("does not add", result["warning"])

if __name__ == "__main__":
    unittest.main()
