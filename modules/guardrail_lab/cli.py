"""CLI. Uses the repository's existing provider adapter when installed in-repo."""
import argparse, json, os, sys
from .cases import CASES
from .runner import run_suite, write_report

def _adapter(provider, model):
    try:
        from modules.ai_scanner.providers import call_provider_messages
    except ImportError as exc:
        raise RuntimeError("Could not import modules.ai_scanner.providers. Run this from the repository root or install the project.") from exc
    def call(messages):
        # call_provider_messages returns (model, text, metadata);
        # the runner's call contract is response text only.
        return call_provider_messages(provider, messages, model=model)[1]
    return call

def main(argv=None):
    parser = argparse.ArgumentParser(prog="guardrail-lab", description="Authorized AI guardrail robustness tests")
    parser.add_argument("--provider", choices=["openai", "anthropic", "gemini"])
    parser.add_argument("--model", default=None)
    parser.add_argument("--output", default="guardrail-report.json")
    parser.add_argument("--case", action="append", dest="case_ids", help="Case ID; repeat to select multiple. Default: all cases.")
    parser.add_argument("--list", action="store_true", help="List cases without making API calls")
    args = parser.parse_args(argv)
    if args.list:
        for case in CASES:
            print(f"{case.case_id}\t{case.category}")
        return 0
    if not args.provider:
        parser.error("--provider is required")
    if args.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY is not set")
    if args.provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        parser.error("ANTHROPIC_API_KEY is not set")
    if args.provider == "gemini" and not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        parser.error("GEMINI_API_KEY or GOOGLE_API_KEY is not set")
    try:
        report = run_suite(_adapter(args.provider, args.model), provider=args.provider, model=args.model, case_ids=args.case_ids)
        write_report(report, args.output)
    except (RuntimeError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report["summary"], indent=2))
    print(f"Evidence report written to {args.output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
