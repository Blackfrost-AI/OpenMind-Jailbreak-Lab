"""Command-line interface."""
import argparse
from .runner import run


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Run authorized instruction-boundary probes "
            "against an AI API."
        )
    )
    parser.add_argument(
        "--provider",
        required=True,
        choices=("openai", "anthropic", "gemini"),
    )
    parser.add_argument(
        "--model",
        help="Optional provider model identifier.",
    )
    parser.add_argument(
        "--output",
        default="openmind-scan-report.json",
    )
    args = parser.parse_args(argv)
    report, path = run(
        args.provider,
        args.model,
        args.output,
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
