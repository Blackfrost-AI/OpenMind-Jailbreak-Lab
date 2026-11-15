"""Run probes and save reproducible evidence."""
from datetime import datetime, timezone
from pathlib import Path
import json
from .probes import PROBES, evaluate
from .providers import call_provider, ProviderError


def run(provider, model=None, output="openmind-scan-report.json"):
    records = []
    actual_model = model
    for probe in PROBES:
        record = {
            "probe_id": probe["id"],
            "category": probe["category"],
            "description": probe["description"],
            "prompt": probe["prompt"],
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
        }
        try:
            actual_model, response, metadata = call_provider(
                provider,
                probe["prompt"],
                actual_model,
            )
            record["response"] = response
            record["metadata"] = metadata
            record["evaluation"] = evaluate(probe, response)
            record["error"] = None
        except ProviderError as exc:
            record["response"] = None
            record["metadata"] = {}
            record["evaluation"] = {
                "status": "not_run"
            }
            record["error"] = str(exc)
        records.append(record)
    report = {
        "schema_version": "1.1",
        "scanner_version": "0.1.1",
        "provider": provider,
        "model": actual_model,
        "started_at_utc": records[0]["timestamp_utc"],
        "completed_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "authorization": (
            "Operator attests they are authorized to test this API account."
        ),
        "limitations": [
            "Small, non-exhaustive set of harmless text probes.",
            "A canary match is an indicator, not proof of exploitability.",
            "No canary match does not prove the model is secure.",
            "Qualitative probes require human review.",
            "No tools are actually invoked.",
            "The multi-turn probe is a simulated transcript in a single "
            "prompt, not a live multi-turn session.",
        ],
        "results": records,
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report, path
