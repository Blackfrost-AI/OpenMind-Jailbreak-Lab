"""Run probes and save reproducible evidence."""
from datetime import datetime, timezone
from pathlib import Path
import json
from .probes import PROBES, evaluate
from .providers import call_provider, call_provider_messages, ProviderError


def _run_multiturn(provider, probe, model):
    """Run a live multi-turn probe: one API call per turn, each call
    carrying the real conversation so far.

    Returns (model, final_response, final_metadata, extra) where extra
    holds the full transcript and the per-turn responses and metadata.
    Stops early if a turn returns no text.
    """
    history = []
    turn_responses = []
    turn_metadata = []
    response = ""
    metadata = {}
    for turn in probe["turns"]:
        history.append({"role": "user", "content": turn})
        model, response, metadata = call_provider_messages(
            provider, list(history), model,
        )
        turn_responses.append(response)
        turn_metadata.append(metadata)
        history.append({"role": "assistant", "content": response})
        if not response.strip():
            break
    extra = {
        "transcript": history,
        "turn_responses": turn_responses,
        "turn_metadata": turn_metadata,
    }
    return model, response, metadata, extra


def run(provider, model=None, output="openmind-scan-report.json"):
    records = []
    actual_model = model
    for probe in PROBES:
        record = {
            "probe_id": probe["id"],
            "category": probe["category"],
            "description": probe["description"],
            "timestamp_utc": datetime.now(
                timezone.utc
            ).isoformat(),
        }
        try:
            if probe.get("turns"):
                actual_model, response, metadata, extra = _run_multiturn(
                    provider, probe, actual_model,
                )
                record["prompt"] = probe["turns"]
                record["turns"] = probe["turns"]
                record.update(extra)
            else:
                record["prompt"] = probe["prompt"]
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
        "schema_version": "1.2",
        "scanner_version": "0.2.0",
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
            "MULTITURN-001 is a simulated transcript in a single "
            "prompt; MULTITURN-LIVE-001 is a live two-turn session.",
            "Detection is exact canary matching only; it cannot "
            "reliably detect semantic failures such as paraphrased "
            "compliance or reworded disclosures.",
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
