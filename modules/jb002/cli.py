import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = json.loads((ROOT / "cases.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "record.schema.json").read_text(encoding="utf-8"))
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
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def valid_date(text):
    """True only for a real calendar date in YYYY-MM-DD form."""
    if not isinstance(text, str) or not DATE_RE.match(text):
        return False
    try:
        date.fromisoformat(text)
    except ValueError:
        return False
    return True


def validate_record(record, schema=SCHEMA):
    """Validate one observation against record.schema.json (stdlib only).

    Returns a list of error strings; empty means valid. The schema's
    pattern for observed_at checks shape; calendar validity is checked
    here with date.fromisoformat, so 2026-02-30 and 2026-13-01 fail.
    """
    errors = []
    if not isinstance(record, dict):
        return ["record is not an object"]
    for key in schema.get("required", []):
        if key not in record:
            errors.append(f"missing required field: {key}")
    if schema.get("additionalProperties") is False:
        for key in record:
            if key not in schema.get("properties", {}):
                errors.append(f"unexpected field: {key}")
    props = schema.get("properties", {})
    for key, value in record.items():
        spec = props.get(key)
        if spec is None:
            continue
        kind = spec.get("type")
        if kind == "string":
            if not isinstance(value, str):
                errors.append(f"{key}: expected a string")
                continue
            if spec.get("minLength") and len(value.strip()) < spec["minLength"]:
                errors.append(f"{key}: must not be empty")
            if "pattern" in spec and not re.match(spec["pattern"], value):
                errors.append(f"{key}: does not match {spec['pattern']}")
            if "enum" in spec and value not in spec["enum"]:
                errors.append(f"{key}: {value!r} is not one of {spec['enum']}")
        elif kind == "integer":
            if isinstance(value, bool) or not isinstance(value, int):
                errors.append(f"{key}: expected an integer")
                continue
            if "minimum" in spec and value < spec["minimum"]:
                errors.append(f"{key}: must be >= {spec['minimum']}")
    if "observed_at" in record and isinstance(record.get("observed_at"), str):
        if DATE_RE.match(record["observed_at"]) and not valid_date(record["observed_at"]):
            errors.append("observed_at: not a real calendar date")
    case_id = record.get("case_id")
    if isinstance(case_id, str) and re.match(r"^JB002-[0-9]{2}$", case_id):
        case = next((x for x in CASES if x["case_id"] == case_id), None)
        if case is None:
            errors.append(f"case_id: {case_id!r} is not a known JB-002 case")
        elif record.get("test_type") != case["test_type"]:
            errors.append(
                f"test_type: {record.get('test_type')!r} does not match "
                f"case {case_id} ({case['test_type']})"
            )
    return errors


def validate_file(path):
    """Validate every JSONL row in path against the schema.

    Returns (checked, errors) where errors are human-readable strings
    naming the offending line. Blank lines are skipped.
    """
    errors = []
    checked = 0
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            errors.append(f"line {n}: not valid JSON")
            continue
        checked += 1
        for err in validate_record(row):
            errors.append(f"line {n}: {err}")
    return checked, errors


def ask(label, default=None):
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def ask_choice(label, options):
    """Numbered menu that reprompts until a valid number is given."""
    while True:
        value = options.get(ask(label))
        if value is not None:
            return value
        print(f"Invalid choice. Enter one of: {', '.join(sorted(options))}.")


def ask_date(label, default):
    while True:
        value = ask(label, default)
        if valid_date(value):
            return value
        print("Invalid date. Use a real calendar date in YYYY-MM-DD form.")


def ask_count(label, default):
    while True:
        try:
            count = int(ask(label, default))
            if count < 1:
                raise ValueError()
            return count
        except ValueError:
            print("Reproduction count must be an integer >= 1.")


def record():
    print("OpenMind JB-002 observation recorder — enter actual observations only.")
    while True:
        case_id = ask("Case ID")
        case = next((x for x in CASES if x["case_id"] == case_id), None)
        if case:
            break
        print("Unknown case ID.")
    while True:
        provider = ask("Provider (openai/anthropic/google/other)").lower()
        if provider in {"openai", "anthropic", "google", "other"}:
            break
        print("Invalid provider. Use openai, anthropic, google, or other.")
    model = ask("Exact model/version")
    scope = ask("Authorized scope / account or test authorization description")
    transcript = ask("Transcript file path or concise transcript reference")
    output = ask("Exact model output (paste one line; preserve full transcript separately)")
    print("\nOutcome: 1 held_boundary, 2 partial_boundary_failure, 3 boundary_failure, 4 over_refusal, 5 inconclusive")
    outcome = ask_choice("Outcome number", OUTCOMES)
    print("\nEvidence: 1 raw_transcript_saved, 2 independently_reproduced, 3 vendor_disclosed, 4 unverified")
    evidence = ask_choice("Evidence status number", EVIDENCE)
    count = ask_count("Reproduction count", "1")
    observed_at = ask_date("Observed date (YYYY-MM-DD)", date.today().isoformat())
    record = {
        "case_id": case_id,
        "provider": provider,
        "model": model,
        "observed_at": observed_at,
        "test_type": case["test_type"],
        "authorized_scope": scope,
        "input_transcript": f'{case["user_task"]}\n\n{case["document"]}\n\nTranscript reference: {transcript}',
        "model_output": output,
        "expected_boundary": case["expected"],
        "observed_outcome": outcome,
        "evidence_status": evidence,
        "reproduction_count": count,
    }
    errors = validate_record(record)
    if errors:
        print("Observation failed validation and was NOT saved:")
        for err in errors:
            print(f"  - {err}")
        raise SystemExit(1)
    out = Path("records")
    out.mkdir(exist_ok=True)
    target = out / "observations.jsonl"
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"\nSaved one observation to {target}. No result was inferred.")


def main(argv=None):
    p = argparse.ArgumentParser(prog="modules.jb002")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    show = sub.add_parser("prompt")
    show.add_argument("case_id")
    sub.add_parser("record")
    validate = sub.add_parser("validate")
    validate.add_argument("path", nargs="?", default="records/observations.jsonl")
    args = p.parse_args(argv)
    if args.cmd == "list":
        list_cases()
    elif args.cmd == "prompt":
        show_prompt(args.case_id)
    elif args.cmd == "record":
        record()
    elif args.cmd == "validate":
        path = Path(args.path)
        if not path.exists():
            print(f"No observations file at {path}; nothing to validate.")
            return
        checked, errors = validate_file(path)
        if errors:
            print(f"{checked} observation(s) checked, {len(errors)} problem(s):")
            for err in errors:
                print(f"  - {err}")
            raise SystemExit(1)
        print(f"{checked} observation(s) checked, all valid.")
        return


if __name__ == "__main__":
    main()
