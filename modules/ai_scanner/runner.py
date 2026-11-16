"""Run probes and save reproducible evidence."""
from datetime import datetime, timezone
from pathlib import Path
import json
from . import __version__
from .probes import PROBES, evaluate
from .providers import call_provider, call_provider_messages


def _run_multiturn(provider, probe, model, base_url=None,
                  api_key_env="OPENAI_COMPAT_API_KEY"):
    """Run a live multi-turn probe: one API call per turn, each call
    carrying the real conversation so far.

    Returns (model, final_response, final_metadata, extra) where extra
    holds the full transcript and the per-turn responses, metadata, and
    errors. A failed turn stops the session but its error and every
    completed turn are preserved in extra instead of being discarded.
    """
    history = []
    turn_responses = []
    turn_metadata = []
    turn_errors = []
    response = ""
    metadata = {}
    for turn in probe["turns"]:
        history.append({"role": "user", "content": turn})
        try:
            model, response, metadata = call_provider_messages(
                provider, list(history), model,
                base_url=base_url, api_key_env=api_key_env,
            )
        except Exception as exc:
            # Any failure (network, malformed provider response, ...) stops
            # the session, but the error and every completed turn are
            # preserved instead of being discarded.
            turn_errors.append(str(exc))
            break
        turn_errors.append(None)
        turn_responses.append(response)
        turn_metadata.append(metadata)
        history.append({"role": "assistant", "content": response})
        if not response.strip():
            break
    extra = {
        "transcript": history,
        "turn_responses": turn_responses,
        "turn_metadata": turn_metadata,
        "turn_errors": turn_errors,
    }
    return model, response, metadata, extra


def run(provider, model=None, output="openmind-scan-report.json",
        base_url=None, api_key_env="OPENAI_COMPAT_API_KEY"):
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
                    base_url=base_url, api_key_env=api_key_env,
                )
                record["prompt"] = probe["turns"]
                record["turns"] = probe["turns"]
                record.update(extra)
                failed = next(
                    (i for i, err in enumerate(extra["turn_errors"])
                     if err is not None),
                    None,
                )
                if failed is None:
                    record["response"] = response
                    record["metadata"] = metadata
                    record["evaluation"] = evaluate(probe, response)
                    record["error"] = None
                else:
                    record["response"] = None
                    record["metadata"] = (
                        extra["turn_metadata"][-1]
                        if extra["turn_metadata"] else {}
                    )
                    record["error"] = extra["turn_errors"][failed]
                    if failed == 0:
                        record["evaluation"] = {"status": "not_run"}
                    else:
                        record["evaluation"] = {
                            "status": "partial_run",
                            "matched_canaries": [],
                            "note": (
                                f"Turn {failed + 1} failed after {failed} "
                                "completed turn(s); partial transcript "
                                "preserved."
                            ),
                        }
            else:
                record["prompt"] = probe["prompt"]
                actual_model, response, metadata = call_provider(
                    provider,
                    probe["prompt"],
                    actual_model,
                    base_url=base_url,
                    api_key_env=api_key_env,
                )
                record["response"] = response
                record["metadata"] = metadata
                record["evaluation"] = evaluate(probe, response)
                record["error"] = None
        except Exception as exc:
            # A provider failure (including a malformed provider response
            # that is not a ProviderError) records this probe as not run
            # instead of aborting the whole scan and losing the report.
            record["response"] = None
            record["metadata"] = {}
            record["evaluation"] = {
                "status": "not_run"
            }
            record["error"] = str(exc)
        records.append(record)
    report = {
        "schema_version": "1.2",
        "scanner_version": __version__,
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
