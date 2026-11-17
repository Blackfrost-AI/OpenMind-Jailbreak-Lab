from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path

DEFAULT_INDEX = Path("data/source_corpus/source_inventory.jsonl")

def load_index(path: Path = DEFAULT_INDEX) -> list[dict]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {number}: {exc}") from exc
        required = {"id", "path", "bytes", "sha256", "status", "runnable"}
        missing = required - item.keys()
        if missing:
            raise ValueError(f"Line {number} missing fields: {', '.join(sorted(missing))}")
        if item["runnable"] is not False:
            raise ValueError(f"Source inventory entry {item['id']} must remain non-runnable")
        records.append(item)
    ids = [item["id"] for item in records]
    paths = [item["path"] for item in records]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        raise ValueError("Duplicate source IDs or paths in source inventory")
    return records

def review_template(item: dict) -> dict:
    return {
        "source_id": item["id"], "source_path": item["path"],
        "source_sha256": item["sha256"], "reviewer": "", "reviewed_at": "",
        "disposition": "unreviewed", "runnable_approval": False,
        "scope_and_rationale": "", "review_notes": "",
        "warning": "This record is not an executable test. Approval here does not add it to any automated runner."
    }

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Browse the original source corpus inventory (metadata only).")
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    parser.add_argument("--search", help="Case-insensitive search across source ID, path, and status")
    parser.add_argument("--id", dest="source_id", help="Show one exact source record")
    parser.add_argument("--json", action="store_true", help="Emit matching metadata as JSON")
    parser.add_argument("--export-review-template", type=Path, help="Write a blank human-review template for --id")
    parser.add_argument("--verify-archive", type=Path, help="Compare an archive's SHA-256 with the checked-in manifest")
    args = parser.parse_args(argv)
    try:
        records = load_index(args.index)
        if args.verify_archive:
            manifest = json.loads(Path("data/source_corpus/manifest.json").read_text(encoding="utf-8"))
            digest = hashlib.sha256(args.verify_archive.read_bytes()).hexdigest()
            expected = manifest["source_archive_sha256"]
            print(json.dumps({"archive": str(args.verify_archive), "actual_sha256": digest,
                              "expected_sha256": expected, "matches": digest == expected}, indent=2))
            return 0 if digest == expected else 2
        if args.source_id:
            matches = [r for r in records if r["id"].casefold() == args.source_id.casefold()]
        elif args.search:
            needle = args.search.casefold()
            matches = [r for r in records if needle in " ".join(str(r.get(k, "")) for k in ("id", "path", "status")).casefold()]
        else:
            matches = records
        if args.export_review_template:
            if len(matches) != 1:
                parser.error("--export-review-template requires --id matching exactly one source record")
            args.export_review_template.parent.mkdir(parents=True, exist_ok=True)
            args.export_review_template.write_text(json.dumps(review_template(matches[0]), indent=2) + "\\n", encoding="utf-8")
            print(f"Wrote review template: {args.export_review_template}")
            return 0
        if args.json:
            print(json.dumps(matches, indent=2))
        else:
            print(f"{len(matches)} source record(s); metadata only; 0 executable raw records")
            for item in matches:
                print(f"{item['id']}  [{item['status']}]  {item['bytes']:>7} bytes  {item['path']}")
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
