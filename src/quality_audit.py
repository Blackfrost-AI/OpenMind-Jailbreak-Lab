"""Non-destructive benchmark quality audit; reports warnings separately from errors."""
from collections import Counter, defaultdict
import json
import sys
from pathlib import Path

def audit(rows):
    errors, warnings = [], []
    ids = [row.get("id") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate case IDs detected")
    prompts = defaultdict(list)
    for row in rows:
        prompt = row.get("user_prompt")
        if isinstance(prompt, str):
            prompts[" ".join(prompt.casefold().split())].append(row.get("id"))
    for matches in prompts.values():
        if len(matches) > 1:
            warnings.append("duplicate normalized prompt: " + ", ".join(map(str, matches)))
    by_split_family = Counter((row.get("split"), row.get("family")) for row in rows)
    adversarial_families = {family for (split, family), count in by_split_family.items()
                            if split == "adversarial" and count}
    benign_families = {family for (split, family), count in by_split_family.items()
                       if split == "benign" and count}
    if len(benign_families) == 1:
        warnings.append("benign controls use only one family; diversify control task types")
    sparse = sorted(family for family in adversarial_families
                    if by_split_family[("adversarial", family)] == 1)
    if sparse:
        warnings.append("singleton adversarial families need more coverage: " + ", ".join(sparse))
    overlap = adversarial_families & benign_families
    if overlap:
        warnings.append("families appear in both splits; verify split intent: " + ", ".join(sorted(overlap)))
    secret_leaks = [row.get("id") for row in rows
                    if row.get("split") == "benign" and row.get("synthetic_secret") is not None]
    if secret_leaks:
        errors.append("benign controls contain synthetic_secret: " + ", ".join(map(str, secret_leaks)))
    return {
        "schema_version": "1.0",
        "record_count": len(rows),
        "split_counts": dict(Counter(row.get("split") for row in rows)),
        "family_counts": {split: dict(Counter(row.get("family") for row in rows if row.get("split") == split))
                          for split in ("adversarial", "benign")},
        "errors": errors,
        "warnings": warnings,
        "status": "fail" if errors else ("review" if warnings else "pass"),
    }

def audit_file(path):
    try:
        rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"schema_version": "1.0", "record_count": 0, "errors": [str(exc)],
                "warnings": [], "status": "fail"}
    return audit(rows)

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "data/benchmark_v0.6.1.jsonl"
    result = audit_file(target)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if result["status"] == "fail" else 0)
