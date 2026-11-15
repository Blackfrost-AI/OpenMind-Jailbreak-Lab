"""Dependency-free validator for OpenMind JSONL benchmark files."""
import json
import re
import sys
from pathlib import Path

REQUIRED = {"id", "family", "split", "risk_level", "user_prompt", "expected_behavior", "tags"}
ALLOWED = REQUIRED | {"synthetic_secret"}
VALID_SPLITS = {"adversarial", "benign"}
VALID_RISK_LEVELS = {"low", "medium"}


def validate(path):
    """Return (parsed_rows, errors) for a JSONL benchmark file."""
    errors, seen, rows = [], set(), []
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        return rows, [f"could not read dataset: {exc}"]

    for line_no, raw in enumerate(lines, 1):
        if not raw.strip():
            errors.append(f"line {line_no}: blank lines are not allowed")
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc}")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {line_no}: record must be an object")
            continue

        missing = REQUIRED - row.keys()
        extra = row.keys() - ALLOWED
        if missing:
            errors.append(f"line {line_no}: missing fields {sorted(missing)}")
        if extra:
            errors.append(f"line {line_no}: unknown fields {sorted(extra)}")

        rid = row.get("id")
        if not isinstance(rid, str) or not re.fullmatch(r"OM-\d{3}", rid):
            errors.append(f"line {line_no}: invalid id")
        elif rid in seen:
            errors.append(f"line {line_no}: duplicate id {rid}")
        else:
            seen.add(rid)

        if row.get("split") not in VALID_SPLITS:
            errors.append(f"line {line_no}: invalid split")
        if row.get("risk_level") not in VALID_RISK_LEVELS:
            errors.append(f"line {line_no}: invalid risk_level")

        family = row.get("family")
        if not isinstance(family, str) or len(family.strip()) < 3:
            errors.append(f"line {line_no}: family must contain at least 3 non-whitespace characters")
        for key in ("user_prompt", "expected_behavior"):
            value = row.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"line {line_no}: {key} must be non-empty text")

        tags = row.get("tags")
        if (not isinstance(tags, list) or not tags
                or not all(isinstance(tag, str) and tag.strip() for tag in tags)):
            errors.append(f"line {line_no}: tags must be a non-empty array of non-blank strings")

        secret = row.get("synthetic_secret")
        if secret is not None and not isinstance(secret, str):
            errors.append(f"line {line_no}: synthetic_secret must be a string or null")
        if row.get("split") == "benign" and secret is not None:
            errors.append(f"line {line_no}: benign control must not carry a synthetic secret")

        rows.append(row)

    if not rows:
        errors.append("dataset must contain at least one valid record")
    else:
        counts = {split: sum(row.get("split") == split for row in rows)
                  for split in VALID_SPLITS}
        if not all(counts.values()):
            errors.append("dataset must include both adversarial and benign cases")
    return rows, errors


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_v0.5.jsonl"
    rows, errors = validate(target)
    print(
        f"records={len(rows)} "
        f"adversarial={sum(row.get('split') == 'adversarial' for row in rows)} "
        f"benign={sum(row.get('split') == 'benign' for row in rows)}"
    )
    if errors:
        print("VALIDATION FAILED\n" + "\n".join(errors))
        sys.exit(1)
    print("VALIDATION PASSED")
