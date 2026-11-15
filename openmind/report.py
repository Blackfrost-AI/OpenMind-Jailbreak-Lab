"""Summarize observed OpenMind guardrail research records."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

def load_records(path):
    records = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{line_no}: invalid JSON: {exc}")
        for key in ("case_id", "provider", "model", "test_type", "observed_outcome", "evidence_status"):
            if key not in item:
                raise SystemExit(f"{path}:{line_no}: missing required field {key!r}")
        records.append(item)
    return records

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python -m openmind.report PATH.jsonl")
    records = load_records(sys.argv[1])
    print(f"Records: {len(records)}")
    if not records:
        return
    providers = defaultdict(Counter)
    families = defaultdict(Counter)
    evidence = Counter()
    for r in records:
        providers[r["provider"]][r["observed_outcome"]] += 1
        families[r["test_type"]][r["observed_outcome"]] += 1
        evidence[r["evidence_status"]] += 1
    print("\nBy provider:")
    for provider, outcomes in sorted(providers.items()):
        print(f"  {provider}: " + ", ".join(f"{k}={v}" for k, v in sorted(outcomes.items())))
    print("\nBy test family:")
    for family, outcomes in sorted(families.items()):
        print(f"  {family}: " + ", ".join(f"{k}={v}" for k, v in sorted(outcomes.items())))
    print("\nEvidence status:")
    for status, count in sorted(evidence.items()):
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()
