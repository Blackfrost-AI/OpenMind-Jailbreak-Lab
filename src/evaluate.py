"""Validate JSONL and optionally summarize reviewer scores."""
import argparse, csv, json, statistics
from collections import defaultdict
from pathlib import Path
from scoring import Scores

def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as stream:
        for line_no, line in enumerate(stream, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            required = {"id","family","family_name","slug","prompt","expected_behavior","risk_level","tags","version"}
            missing = required - row.keys()
            if missing:
                raise ValueError(f"Line {line_no}: missing {sorted(missing)}")
            if row["risk_level"] != "benign":
                raise ValueError(f"Line {line_no}: non-benign record rejected")
            rows.append(row)
    return rows

def summarize(path):
    grouped = defaultdict(list)
    with open(path, newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            grouped[row["family"]].append(Scores(*(int(row[k]) for k in
                ("hierarchy","boundary","utility","calibration"))))
    report = {}
    for family, items in sorted(grouped.items()):
        report[family] = {
            "n": len(items),
            "mean_total": round(statistics.mean(s.total for s in items), 2),
            "robust_pass_rate": round(sum(s.outcome == "robust_pass" for s in items)/len(items), 3),
            "failure_rate": round(sum(s.outcome == "failure" for s in items)/len(items), 3)
        }
    return report

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", default="data/benchmark_v0.2.jsonl")
    parser.add_argument("--scores", help="Optional reviewer CSV to summarize")
    args = parser.parse_args()
    rows = load_jsonl(args.validate)
    print(f"VALID: {len(rows)} records; {len(set(r['family'] for r in rows))} families")
    if args.scores:
        print(json.dumps(summarize(args.scores), indent=2))

if __name__ == "__main__":
    main()
