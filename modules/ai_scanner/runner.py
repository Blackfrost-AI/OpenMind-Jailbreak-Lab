"""Run probes and save reproducible evidence."""
from datetime import datetime, timezone
from pathlib import Path
import json
import time
from . import __version__
from .probes import PROBES, evaluate
from .providers import ProviderError, call_provider, call_provider_messages

def _error_details(exc):
    if isinstance(exc, ProviderError):
        return exc.as_dict()
    return {"category": "unexpected", "code": "unexpected_error",
            "http_status": None, "retryable": False, "message": str(exc)}


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
    turn_error_details = []
    response = ""
    metadata = {}
    for turn in probe["turns"]:
        history.append({"role": "user", "content": turn})
        try:
            (
                model, response, metadata, attempts, inconclusive
            ) = _call_with_incomplete_retry(
                call_provider_messages,
                provider, list(history), model,
                base_url=base_url, api_key_env=api_key_env,
            )
        except Exception as exc:
            # Any failure (network, malformed provider response, ...) stops
            # the session, but the error and every completed turn are
            # preserved instead of being discarded.
            turn_errors.append(str(exc))
            turn_error_details.append(_error_details(exc))
            break
        turn_errors.append(None)
        turn_error_details.append(None)
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
        "turn_error_details": turn_error_details,
    }
    return model, response, metadata, extra


def _provider_response_status(response, metadata, error=None):
    """Classify transport/output completeness separately from probe scoring.

    A non-empty response is reported as text_returned, not guaranteed
    semantically complete. Only explicit provider metadata can establish
    an incomplete generation; an empty body without an error is empty.
    """
    if error is not None:
        return "not_received"
    metadata = metadata if isinstance(metadata, dict) else {}
    status = str(metadata.get("status") or "").casefold()
    stop_reason = str(
        metadata.get("stop_reason") or metadata.get("finish_reason") or ""
    ).casefold()
    if status in {"incomplete", "failed", "cancelled", "canceled"}:
        return "incomplete"
    if stop_reason in {"max_tokens", "max_output_tokens", "length"}:
        return "incomplete"
    if not isinstance(response, str) or not response.strip():
        return "empty"
    return "text_returned"


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
                inconclusive_turn = next(
                    (i for i, value in enumerate(extra["turn_inconclusive"])
                     if value),
                    None,
                )
                if failed is None and inconclusive_turn is None:
                    record["response"] = response
                    record["metadata"] = metadata
                    record["evaluation"] = evaluate(probe, response)
                    record["error"] = None
                    record["error_details"] = None
                elif failed is None:
                    record["response"] = response
                    record["metadata"] = metadata
                    record["evaluation"] = {
                        "status": "inconclusive",
                        "matched_canaries": [],
                        "note": (
                            f"Turn {inconclusive_turn + 1} remained incomplete "
                            "after the bounded retry policy; no pass/fail "
                            "judgment was made."
                        ),
                    }
                    record["error"] = None
                    record["error_details"] = None
                else:
                    record["response"] = None
                    record["metadata"] = (
                        extra["turn_metadata"][-1]
                        if extra["turn_metadata"] else {}
                    )
                    record["error"] = extra["turn_errors"][failed]
                    record["error_details"] = extra["turn_error_details"][failed]
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
                (
                    actual_model, response, metadata, attempts, inconclusive
                ) = _call_with_incomplete_retry(
                    call_provider,
                    provider,
                    probe["prompt"],
                    actual_model,
                    base_url=base_url,
                    api_key_env=api_key_env,
                )
                record["response_attempts"] = attempts
                record["response"] = response
                record["metadata"] = metadata
                if inconclusive:
                    record["evaluation"] = {
                        "status": "inconclusive",
                        "matched_canaries": [],
                        "note": (
                            "Provider generation remained incomplete after "
                            "the bounded retry policy; no pass/fail "
                            "judgment was made."
                        ),
                    }
                else:
                    record["evaluation"] = evaluate(probe, response)
                record["error"] = None
                record["error_details"] = None
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
            record["error_details"] = _error_details(exc)
        records.append(record)

    for record in records:
        if (
            record.get("turn_errors")
            and record.get("turn_responses")
            and record.get("error")
        ):
            record["provider_response_status"] = "partial"
        else:
            record["provider_response_status"] = _provider_response_status(
                record.get("response"),
                record.get("metadata"),
                record.get("error"),
            )
    response_statuses = [
        item["provider_response_status"] for item in records
    ]

    report = {
        "schema_version": "1.3",
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
            "Detection distinguishes a response that is only a canary "
            "from a canary mentioned in a longer response; it cannot "
            "reliably detect semantic failures such as paraphrased "
            "compliance or reworded disclosures.",
        ],
        "summary": {
            "total_probes": len(records),
            # Legacy field: this means the probe execution/evaluation path ran,
            # not that the provider necessarily returned a complete response.
            "completed": sum(
                item["evaluation"]["status"] not in ("not_run", "partial_run")
                for item in records
            ),
            "probe_executions_completed": sum(
                item["evaluation"]["status"] not in ("not_run", "partial_run")
                for item in records
            ),
            "provider_responses_completed": response_statuses.count("text_returned"),
            "provider_responses_incomplete": response_statuses.count("incomplete"),
            "inconclusive": sum(
                item["evaluation"]["status"] == "inconclusive"
                for item in records
            ),
            "provider_responses_partial": response_statuses.count("partial"),
            "provider_responses_empty": response_statuses.count("empty"),
            "provider_responses_not_received": response_statuses.count("not_received"),
            "partial": sum(
                item["evaluation"]["status"] == "partial_run"
                for item in records
            ),
            "not_run": sum(
                item["evaluation"]["status"] == "not_run"
                for item in records
            ),
            "errors": sum(item.get("error") is not None for item in records),
            "completion_note": (
                "completed/probe_executions_completed counts probes whose "
                "request/evaluation path ran. provider_responses_completed "
                "counts non-empty text responses only; text_returned does "
                "not guarantee semantic completeness."
            ),
        },
        "results": records,
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report, path


INCOMPLETE_RESPONSE_RETRIES = 1
INCOMPLETE_RESPONSE_RETRY_DELAY_SECONDS = 0.5


def _incomplete_retryable(metadata):
    """Retry only ambiguous incomplete generations, never known hard stops."""
    metadata = metadata if isinstance(metadata, dict) else {}
    status = str(metadata.get("status") or "").casefold()
    reason = str(
        metadata.get("stop_reason")
        or metadata.get("finish_reason")
        or ""
    ).casefold()
    details = metadata.get("incomplete_details")
    if isinstance(details, dict):
        detail_reason = str(details.get("reason") or "").casefold()
        if detail_reason in {
            "max_output_tokens", "max_tokens", "length",
            "content_filter", "safety",
        }:
            return False
    if reason in {
        "max_output_tokens", "max_tokens", "length",
        "content_filter", "safety", "refusal",
    }:
        return False
    return status == "incomplete" or reason in {"error", "other"}


def _call_with_incomplete_retry(call, *args, **kwargs):
    """Retry one ambiguous incomplete generation once and preserve attempts.

    Known output-limit and safety stops are not retried. A response is
    usable only when the final attempt is not explicitly incomplete.
    """
    attempts = []
    for attempt_number in range(1, INCOMPLETE_RESPONSE_RETRIES + 2):
        model, response, metadata = call(*args, **kwargs)
        metadata = metadata if isinstance(metadata, dict) else {}
        attempts.append({
            "attempt": attempt_number,
            "response": response,
            "metadata": metadata,
        })
        status = _provider_response_status(response, metadata)
        if status != "incomplete":
            return model, response, metadata, attempts, False
        if (
            attempt_number > INCOMPLETE_RESPONSE_RETRIES
            or not _incomplete_retryable(metadata)
        ):
            return model, response, metadata, attempts, True
        time.sleep(INCOMPLETE_RESPONSE_RETRY_DELAY_SECONDS)
    raise AssertionError("unreachable retry loop")

