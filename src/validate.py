"""Dependency-free validator for OpenMind JSONL benchmark files."""
import json, re, sys
from pathlib import Path

REQUIRED = {"id", "family", "split", "risk_level", "user_prompt", "expected_behavior", "tags"}
ALLOWED = REQUIRED | {"synthetic_secret"}

def validate(path):
    errors, seen, rows = [], set(), []
    for line_no, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            errors.append(f"line {line_no}: blank lines are not allowed")
            continue
        try: row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc}"); continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: record must be an object"); continue
        missing, extra = REQUIRED-row.keys(), row.keys()-ALLOWED
        if missing: errors.append(f"line {line_no}: missing fields {sorted(missing)}")
        if extra: errors.append(f"line {line_no}: unknown fields {sorted(extra)}")
        rid = row.get("id")
        if not isinstance(rid, str) or not re.fullmatch(r"OM-\d{3}", rid): errors.append(f"line {line_no}: invalid id")
        elif rid in seen: errors.append(f"line {line_no}: duplicate id {rid}")
        else: seen.add(rid)
        if row.get("split") not in ("adversarial", "benign"): errors.append(f"line {line_no}: invalid split")
        if row.get("risk_level") not in ("low", "medium"): errors.append(f"line {line_no}: invalid risk_level")
        for key in ("family", "user_prompt", "expected_behavior"):
            if not isinstance(row.get(key), str) or not row[key].strip(): errors.append(f"line {line_no}: {key} must be non-empty text")
        if not isinstance(row.get("tags"), list) or not row["tags"] or not all(isinstance(x, str) and x for x in row["tags"]): errors.append(f"line {line_no}: tags must be a non-empty string array")
        if row.get("split") == "benign" and row.get("synthetic_secret") is not None: errors.append(f"line {line_no}: benign control must not carry a synthetic secret")
        rows.append(row)
    ids = [r.get("id") for r in rows if isinstance(r, dict)]
    if ids and len(ids) != len(set(ids)): pass
    if rows:
        counts = {s: sum(r.get("split") == s for r in rows) for s in ("adversarial", "benign")}
        if not all(counts.values()): errors.append("dataset must include both adversarial and benign cases")
    return rows, errors

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_v0.3.jsonl"
    rows, errors = validate(target)
    print(f"records={len(rows)} adversarial={sum(r.get('split')=='adversarial' for r in rows)} benign={sum(r.get('split')=='benign' for r in rows)}")
    if errors:
        print("VALIDATION FAILED\n" + "\n".join(errors)); sys.exit(1)
    print("VALIDATION PASSED")
