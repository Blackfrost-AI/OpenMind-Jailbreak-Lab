"""Command-line interface."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .runner import run


def _load_report(path):
    """Load one saved scan report, raising ValueError with a readable
    message when the file is missing, unreadable, or malformed."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"cannot read report {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"report {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"report {path} must be a JSON object")
    results = data.get("results", [])
    if not isinstance(results, list):
        raise ValueError(f"report {path}: 'results' must be a list")
    for item in results:
        if not isinstance(item, dict) or not isinstance(item.get("probe_id"), str):
            raise ValueError(
                f"report {path}: each result needs a string 'probe_id'")
        evaluation = item.get("evaluation")
        if not isinstance(evaluation, dict) or not isinstance(
                evaluation.get("status"), str):
            raise ValueError(
                f"report {path}: result {item.get('probe_id')!r} needs "
                "'evaluation' with a string 'status'")
    return data


def compare_reports(paths, output):
    """Combine per-provider scan reports into one comparison.

    Prints a probe-by-provider status matrix and writes a consolidated
    JSON file. A provider that was scanned twice (different models)
    gets a second column named provider/model.
    """
    providers = []
    by_probe = {}
    for path in paths:
        try:
            data = _load_report(path)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        provider = data.get("provider")
        if not isinstance(provider, str) or not provider:
            provider = Path(path).stem
        model = data.get("model")
        if not isinstance(model, str):
            model = None
        column = provider
        suffix = 0
        while any(p["column"] == column for p in providers):
            suffix += 1
            base = f"{provider}/{model}" if model else f"{provider}/{path}"
            column = base if suffix == 1 else f"{base}#{suffix}"
        providers.append({"column": column, "provider": provider,
                          "model": model, "path": str(path)})
        for item in data.get("results", []):
            by_probe.setdefault(item["probe_id"], {})[column] = {
                "status": item["evaluation"]["status"],
                "model": model,
                "error": item.get("error"),
            }
    comparison = {
        "schema_version": "1.0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "providers": providers,
        "probes": by_probe,
    }
    header = "Probe".ljust(22) + "".join(
        p["column"].ljust(22) for p in providers
    )
    print(header)
    for probe_id in sorted(by_probe):
        row = "".join(
            by_probe[probe_id].get(p["column"], {}).get("status", "-").ljust(22)
            for p in providers
        )
        print(probe_id.ljust(22) + row)
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(comparison, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Saved comparison: {out}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Run authorized instruction-boundary probes "
            "against an AI API, or compare saved scan reports."
        )
    )
    parser.add_argument(
        "--provider",
        choices=("openai", "anthropic", "gemini", "openai-compatible"),
        help="Provider to scan (run mode).",
    )
    parser.add_argument(
        "--model",
        help="Optional provider model identifier.",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible API base URL "
             "(openai-compatible provider only).",
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_COMPAT_API_KEY",
        help="Environment variable holding the compatible endpoint API "
             "key; may be empty for local servers "
             "(openai-compatible provider only).",
    )
    parser.add_argument(
        "--output",
        default="openmind-scan-report.json",
        help="Report destination (run mode).",
    )
    sub = parser.add_subparsers(dest="cmd")
    compare = sub.add_parser(
        "compare",
        help="Compare saved scan reports across providers.",
    )
    compare.add_argument("reports", nargs="+")
    compare.add_argument(
        "--output",
        default="reports/comparison.json",
        help="Consolidated comparison destination.",
    )
    args = parser.parse_args(argv)
    if args.cmd == "compare":
        return compare_reports(args.reports, args.output)
    if not args.provider:
        parser.error("--provider is required")
    if args.provider == "openai-compatible":
        import os
        if not (args.base_url or os.getenv("OPENAI_COMPAT_BASE_URL")):
            parser.error(
                "Set --base-url or OPENAI_COMPAT_BASE_URL for this provider"
            )
        if not (args.model or os.getenv("OPENAI_COMPAT_MODEL")):
            parser.error("Set --model or OPENAI_COMPAT_MODEL for this provider")
    report, path = run(
        args.provider,
        args.model,
        args.output,
        base_url=args.base_url,
        api_key_env=args.api_key_env,
    )
    counts = {}
    for item in report["results"]:
        status = item["evaluation"]["status"]
        counts[status] = counts.get(status, 0) + 1
    print(f"Saved evidence report: {path}")
    print(
        "Result counts:",
        ", ".join(
            f"{key}={value}"
            for key, value in sorted(counts.items())
        ),
    )
    if any(item["error"] for item in report["results"]):
        return 1
    return 0
