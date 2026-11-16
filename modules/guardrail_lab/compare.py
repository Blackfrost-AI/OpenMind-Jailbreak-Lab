"""Compare saved Guardrail Lab reports without collapsing provider-specific outcomes."""
import argparse
import json
from pathlib import Path

def compare_reports(reports):
    if len(reports) < 2:
        raise ValueError("at least two reports are required")
    indexed = []
    source_labels = set()
    for report in reports:
        results = report.get("results")
        if not isinstance(results, list):
            raise ValueError("each report must contain a results array")
        mapping = {}
        for item in results:
            case_id = item.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                raise ValueError("every result must have a non-empty case_id")
            if case_id in mapping:
                raise ValueError("duplicate case_id in report: " + case_id)
            mapping[case_id] = item.get("assessment", "unknown")
        provider = report.get("provider", "unknown")
        model = report.get("model")
        label = f"{provider}/{model or 'unspecified'}"
        if label in source_labels:
            raise ValueError("duplicate provider/model report label: " + label)
        source_labels.add(label)
        indexed.append((provider, model, mapping))
    common = set.intersection(*(set(item[2]) for item in indexed))
    union = set.union(*(set(item[2]) for item in indexed))
    rows, disagreements = [], []
    for case_id in sorted(union):
        outcomes = {f"{provider}/{model or 'unspecified'}": mapping.get(case_id)
                    for provider, model, mapping in indexed}
        present = [value for value in outcomes.values() if value is not None]
        agree = len(present) == len(outcomes) and len(set(present)) == 1
        rows.append({"case_id": case_id, "outcomes": outcomes, "agreement": agree})
        if not agree:
            disagreements.append(case_id)
    agreement_rate = (sum(row["agreement"] for row in rows if row["case_id"] in common) / len(common)
                      if common else None)
    return {
        "schema_version": "1.0",
        "providers": [{"provider": p, "model": m, "case_count": len(mapping)}
                      for p, m, mapping in indexed],
        "common_case_count": len(common),
        "union_case_count": len(union),
        "missing_case_ids": {f"{p}/{m or 'unspecified'}": sorted(union - set(mapping))
                             for p, m, mapping in indexed},
        "agreement_rate_on_common_cases": agreement_rate,
        "disagreement_or_missing_case_ids": disagreements,
        "cases": rows,
        "interpretation": "Agreement compares automated labels only; it is not a security score or proof of equivalent model behavior. Review full transcripts and normalize run conditions before drawing conclusions.",
    }

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", help="two or more Guardrail Lab JSON report paths")
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args(argv)
    try:
        reports = [json.loads(Path(path).read_text(encoding="utf-8")) for path in args.reports]
        result = compare_reports(reports)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(rendered + "\\n", encoding="utf-8")
    else:
        print(rendered)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
