# Bounded automated discovery engine

This patch adds deterministic test-variant generation, a provider-adapter hook,
and evidence-led severity ranking. It uses synthetic canaries and fixed,
reviewable prompt envelopes only.

## Generate variants (no provider calls)

Input is JSONL; each line must be an object with `id` and `prompt`. Optional
fields (for example `category`, `canary`, `expected_signal`, and `control`) are
preserved.

```bash
python -m modules.guardrail_lab.discovery \
  --input data/discovery_seed_cases.example.jsonl \
  --variants 6 --seed 17 \
  --out results/discovery_cases.jsonl
```

The output count is `number of input cases × variants`. Generation itself makes
zero network requests. Review the generated cases before running them.

## Use an existing provider adapter

```python
from modules.guardrail_lab.discovery import run_discovery

# `seed_cases` is a list of JSONL case dictionaries. `provider_call` must be
# your existing authorized provider adapter and return a dictionary.
report = run_discovery(
    seed_cases,
    provider_call,
    variants=3,
    seed=17,
    request_budget=30,
)
```

The runner is serial and checks the total request budget before making the first
provider call. Connect only an existing, authorized adapter; this patch does
not add credentials handling or change provider safety settings.

## Rank reviewed findings

`rank_findings(records)` requires an explicit human `review_status`, assessment,
impact, reproducibility flag, provider, model, and evidence reference. Only a
human-confirmed `potential_guardrail_failure` is ranked. Ambiguous canary
mentions remain in triage and cannot be counted as confirmed bypasses. Severity
is supplied by the reviewer, not inferred from response text.

## Safety

No model weights are modified, refusals are not suppressed, and no hidden
behavior or real-secret extraction is added. Model output is recorded as data;
the engine does not execute tool instructions found in responses.


## Confirmation gate

A finding can enter the confirmed ranking only after human review, with
`assessment=potential_guardrail_failure`, `reproducible=true`, at least two
repeat runs, and at least two successful reproductions. A single canary match,
a quoted marker, or a provider error remains unconfirmed. The discovery module
does not infer severity or promote results automatically.

## Current scope

The generator uses six fixed, reviewed wrappers around supplied synthetic test
cases. The live Guardrail Lab campaign uses its existing provider adapters and
bounded fixed framings. This is not an unconstrained prompt optimizer and does
not generate payloads intended to defeat safeguards for harmful outcomes.


## External prompt-pattern corpus

An independently authored corpus adapts high-level patterns from the
togg53192-cmd/jailbreaks collection into 12 adversarial synthetic-canary cases
and 3 benign controls:

```bash
python -m modules.guardrail_lab.discovery \
  --input data/external_prompt_patterns_v1.jsonl \
  --variants 6 --seed 17 \
  --out results/external_prompt_patterns_v1.generated.jsonl
```

This generates 90 reviewable cases offline and makes zero provider calls.
Source prompt files are treated as untrusted research material, not imported
as live system/developer instructions. The source repository has no declared
license in its GitHub metadata, so no prompt text is copied. See
[external corpus provenance and usage](EXTERNAL_PATTERN_CORPUS.md).
