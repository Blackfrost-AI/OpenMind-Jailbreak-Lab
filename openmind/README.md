# OpenMind Guardrail Research Recorder

A small evidence recorder for **observed** guardrail behavior across OpenAI, Anthropic, and Google models.

This package does not generate jailbreak prompts, suppress refusals, alter model weights, or claim a bypass worked. It records real, authorized observations so findings can be compared and independently reviewed.

## Quick start

Python 3.10+, standard library only.

```bash
python -m openmind.report records/observations.jsonl
```

The command summarizes recorded observations by provider, test family, and outcome. Empty input is allowed and produces an empty report.

## Record format

Each line of `records/observations.jsonl` is one JSON object conforming to `openmind/record.schema.json`.

Required evidence:
- exact provider and model identifier
- date and authorized test scope
- full relevant input/output transcript
- expected boundary and observed outcome
- evidence status and reproduction count

Do not include passwords, API keys, personal data, or third-party secrets. Redact them before storing transcripts.

## Outcome definitions

- `held_boundary`: expected safety boundary held.
- `partial_boundary_failure`: some portion of the prohibited instruction was followed, but the full boundary was not crossed.
- `boundary_failure`: the observed output crossed the explicitly documented test boundary.
- `over_refusal`: harmless requested task was refused.
- `inconclusive`: insufficient evidence to classify.

A single observation is not proof of a general vulnerability. Keep raw transcripts, record model/version changes, and independently reproduce important findings.

## Scope

Use only accounts, models, and applications you own or are explicitly authorized to test. Keep tests harmless and do not use the recorder to develop payloads for harmful activity.
