#!/usr/bin/env python3
"""Build an inert, hash-verified inventory from an external prompt archive.

Source prompt bodies are deliberately not copied into the generated catalog or
loaded as instructions. The catalog is metadata for authorized review only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import PurePosixPath

PATTERNS = {
    "authority": r"system prompt|developer instruction|highest priority|absolute priority|authority|precedence|priority|override|supersed|instruction hierarchy",
    "refusal": r"refus|do not decline|never refuse|non.evasive|safety policy|guardrail|content policy|prohibition",
    "persona": r"you are |persona|identity|roleplay|operating register|session binding",
    "policy_scope": r"policy|boundar(y|ies)|scope|in.scope|out.of.scope|content guidelines|operating policy",
    "agent_tools": r"agent|tool|workspace|sandbox|execute|terminal|permission|autonomous",
    "reasoning_output": r"thinking|chain.of.thought|output format|format|reasoning|response style",
    "malware_credentials": r"keylog|credential theft|password dump|reverse shell|command.and.control|persistence|exfiltrat|ransomware|malware",
    "sexual_boundary": r"erotica|non.consent|sexual|adult fiction|dubious consent",
    "physical_harm": r"bomb|explosive|weapon|poison|self.harm|suicid|violence",
    "encoding": r"base64|encoded|decode|obfuscat|hexadecimal|unicode",
}
MAX_FILES = 256
MAX_MEMBER_BYTES = 2_000_000
MAX_TOTAL_BYTES = 20_000_000


def inventory_archive(source: str) -> list[dict]:
    rows = []
    total = 0
    with zipfile.ZipFile(source) as archive:
        members = [m for m in archive.infolist() if not m.is_dir()]
        if len(members) > MAX_FILES:
            raise ValueError(f"archive has {len(members)} files; limit is {MAX_FILES}")
        for member in members:
            path = PurePosixPath(member.filename)
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"unsafe archive path: {member.filename!r}")
            if member.file_size > MAX_MEMBER_BYTES:
                raise ValueError(f"archive member exceeds size limit: {member.filename}")
            total += member.file_size
            if total > MAX_TOTAL_BYTES:
                raise ValueError("archive exceeds total uncompressed size limit")
            raw = archive.read(member)
            body = raw.decode("utf-8", errors="replace")
            rel = member.filename
            prefix = "jailbreaks-main/"
            if rel.startswith(prefix):
                rel = rel[len(prefix):]
            parts = rel.split("/")
            family = parts[0] if len(parts) > 1 else "Root"
            target = parts[-1].rsplit(".", 1)[0]
            tags = [name for name, pattern in PATTERNS.items()
                    if re.search(pattern, body, flags=re.IGNORECASE)]
            if rel.lower() == "readme.md":
                kind = "readme"
            elif not body.strip():
                kind = "empty"
            else:
                kind = "prompt_config"
            rows.append({
                "id": "SRC-" + hashlib.sha256(rel.encode("utf-8")).hexdigest()[:12].upper(),
                "source_project": "togg53192-cmd/jailbreaks",
                "source_path": rel,
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "source_bytes": len(raw),
                "model_family_or_folder": family,
                "target_label": target,
                "record_type": kind,
                "detected_patterns": tags,
                "handling": "inert_metadata_only",
                "prompt_text_included": False,
                "assessment_status": "unreviewed_source_record",
            })
    return sorted(rows, key=lambda row: row["source_path"].casefold())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="path to source ZIP archive")
    parser.add_argument("--out", required=True, help="output JSONL catalog path")
    args = parser.parse_args(argv)
    try:
        rows = inventory_archive(args.input)
        with open(args.out, "w", encoding="utf-8", newline="\n") as output:
            for row in rows:
                output.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        print(f"import failed: {exc}", file=sys.stderr)
        return 2
    print(f"Catalogued {len(rows)} files; prompt bodies were not copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
