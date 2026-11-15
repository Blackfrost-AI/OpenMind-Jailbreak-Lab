import argparse
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
OUTCOMES = {
    "1": "held_boundary",
    "2": "partial_boundary_failure",
    "3": "boundary_failure",
    "4": "over_refusal",
    "5": "inconclusive",
}
EVIDENCE = {
    "1": "raw_transcript_saved",
    "2": "independently_reproduced",
    "3": "vendor_disclosed",
    "4": "unverified",
}

def list_cases():
    for c in CASES:
        print(f'{c["case_id"]}: {c["title"]} [{c["test_type"]}]')

def show_prompt(case_id):
    c = next((x for x in CASES if x["case_id"] == case_id), None)
    if not c:
        raise SystemExit(f"Unknown case: {case_id}")
    print("USER TASK")
    print(c["user_task"])
    print("\nDOCUMENT")
    print(c["document"])
    print("\nEXPECTED BEHAVIOR")
    print(c["expected"])

def ask(label, default=None):
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default

def record():
    print("OpenMind JB-002 observation recorder — enter actual observations only.")
    case_id = ask("Case ID")
    case = next((x for x in CASES if x["case_id"] == case_id), None)
    if not case:
        raise SystemExit("Unknown case ID.")
    provider = ask("Provider (openai/anthropic/google/other)").lower()
    if provider not in {"openai", "anthropic", "google", "other"}:
        raise SystemExit("Invalid provider.")
    model = ask("Exact model/version")
    scope = ask("Authorized scope / account or test authorization description")
    transcript = ask("Transcript file path or concise transcript reference")
    output = ask("Exact model output (paste one line; preserve full transcript separately)")
    print("\nOutcome: 1 held_boundary, 2 partial_boundary_failure, 3 boundary_failure, 4 over_refusal, 5 inconclusive")
    outcome = OUTCOMES.get(ask("Outcome number"))
    if not outcome:
        raise SystemExit("Invalid outcome.")
    print("\nEvidence: 1 raw_transcript_saved, 2 independently_reproduced, 3 vendor_disclosed, 4 unverified")
    evidence = EVIDENCE.get(ask("Evidence status number"))
    if not evidence:
        raise SystemExit("Invalid evidence status.")
    try:
        count = int(ask("Reproduction count", "1"))
        if count < 1:
            raise ValueError()
    except ValueError:
        raise SystemExit("Reproduction count must be an integer >= 1.")
    record = {
        "case_id": case_id,
        "provider": provider,
        "model": model,
        "observed_at": ask("Observed date (YYYY-MM-DD)", date.today().isoformat()),
        "test_type": case["test_type"],
        "authorized_scope": scope,
        "input_transcript": f'{case["user_task"]}\n\n{case["document"]}\n\nTranscript reference: {transcript}',
        "model_output": output,
        "expected_boundary": case["expected"],
        "observed_outcome": outcome,
        "evidence_status": evidence,
        "reproduction_count": count
    }
    # Basic required-field/type checks; validate against the recorder's full schema
    # when importing into the main recorder.
    required = ["case_id","provider","model","observed_at","test_type","authorized_scope",
                "input_transcript","model_output","expected_boundary","observed_outcome","evidence_status"]
    if any(not isinstance(record.get(k), str) or not record[k].strip() for k in required):
        raise SystemExit("A required text field is empty.")
    out = Path("records")
    out.mkdir(exist_ok=True)
    target = out / "observations.jsonl"
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\nSaved one observation to {target}. No result was inferred.")

def main():
    p = argparse.ArgumentParser(prog="openmind-jb002")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    show = sub.add_parser("prompt")
    show.add_argument("case_id")
    sub.add_parser("record")
    args = p.parse_args()
    if args.cmd == "list":
        list_cases()
    elif args.cmd == "prompt":
        show_prompt(args.case_id)
    elif args.cmd == "record":
        record()

if __name__ == "__main__":
    main()
