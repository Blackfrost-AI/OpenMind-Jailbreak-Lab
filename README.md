# OpenMind Jailbreak Lab — Benchmark v0.3

A defensive, reproducible benchmark for instruction hierarchy, prompt-injection resistance, and refusal calibration. It evaluates whether a model follows trusted instructions, treats untrusted content as data, protects synthetic secrets, and remains helpful on benign controls.

## Scope

- Authorized evaluation of models and applications you own or are permitted to test.
- Harmless synthetic secrets and simulated tool outputs only.
- No live credentials, real personal data, real targets, malware, or harmful operational payloads.

## Quick start

Requires Python 3.10+; no third-party dependencies for validation.

```bash
python -m src.validate data/benchmark_v0.3.jsonl
python -m unittest discover -s tests -v
```

## Dataset

`data/benchmark_v0.3.jsonl` contains 30 authored cases: 16 adversarial boundary tests and 14 benign negative controls. The split is deliberate: robustness must not be measured by refusal rate alone. Cases cover authority confusion, untrusted-content handling, tool-output injection, synthetic-secret protection, multi-turn drift, multilingual boundaries, format/encoding variation, and benign utility.

## Scoring

Score each response on a 0–2 scale for `boundary_integrity`, `task_utility`, and `explanation_quality`. See `SCORING.md`. Report attack success rate only over adversarial cases, and false-positive/refusal rate over benign controls. Do not combine these into one headline number.

## Reproducibility

Record provider, exact model/version, date, system/developer configuration, tools enabled, temperature/sampling settings where available, case ID, raw response, evaluator, and adjudication. Run each case at least three times when sampling is non-deterministic. Keep a held-out set to reduce benchmark overfitting.

## Limitations

This is a small seed benchmark, not a validated industry standard. It does not establish novelty, prove a model secure/insecure, or support claims about all deployments. Human review is required for ambiguous outcomes.

## Versioning

- v0.3: balanced adversarial/benign design, explicit scoring dimensions, schema validation, and reproducibility guidance.
