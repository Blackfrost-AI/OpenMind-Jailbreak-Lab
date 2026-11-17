"""Load safe, source-attributed adaptations into the Guardrail Lab."""
from __future__ import annotations
import json
from pathlib import Path
from .cases import Case

_DATA = Path(__file__).resolve().parents[2] / "data" / "source_corpus" / "safe_adaptations.jsonl"

def load_source_cases():
    cases = []
    with _DATA.open(encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("runnable") is not True or row.get("adaptation") != "safe_pattern_adaptation":
                raise ValueError(f"unsafe or invalid source case on line {line_no}")
            if not row.get("source_path") or len(row.get("source_sha256", "")) != 64:
                raise ValueError(f"missing provenance on line {line_no}")
            cases.append(Case(row["case_id"], "source_" + row["category"], row["prompt"], row["expected_signal"], row["canary"]))
    return tuple(cases)

SOURCE_CASES = load_source_cases()
