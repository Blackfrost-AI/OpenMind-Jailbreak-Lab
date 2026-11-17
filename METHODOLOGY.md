# Methodology and release gates

1. Freeze the benchmark version and record its SHA-256 before testing.
2. Use identical case text and comparable configurations across providers; document unavoidable differences.
3. Separate adversarial cases from benign controls. Never use refusal rate as a proxy for safety.
4. Run at least three trials for stochastic systems; retain raw outputs.
5. Have two reviewers independently score ambiguous cases, then document adjudication.
6. Report per-family counts, denominators, model/version, date, and confidence intervals where sample size supports them.
7. Keep a held-out set; do not tune the benchmark and report performance on the same cases as independent validation.
8. Do not claim a vulnerability from one response. Reproduce it, minimize it, and state deployment assumptions.

## Release checklist

- [ ] JSONL parses and schema validation passes.
- [ ] IDs are unique and split labels are balanced enough for stated metrics.
- [ ] Every case has an observable expected behavior.
- [ ] Benign controls are included and tested for over-refusal.
- [ ] No real secrets, private data, or live targets appear.
- [ ] Dataset provenance and license are documented.
- [ ] Model versions and test conditions accompany every result.

## Source-derived Guardrail Lab cases

The Guardrail Lab currently contains 76 cases: 24 core instruction-boundary
tests and 52 source-derived safe adaptations. The latter are separately
rewritten test scenarios, not verbatim source prompts. They preserve source ID,
relative path, and SHA-256 provenance while replacing risky instructions with
inert canary markers.

The raw uploaded archive is represented only by a 55-record metadata inventory.
The withdrawn notice, one-byte placeholder, and archive README are not adapted.
At import time, the loader checks the inventory checksum, adaptation schema,
unique case/source/canary IDs, safe test framing, and source ID/path/hash
consistency. Live evidence records include `source_provenance`.

Use `--source-corpus` to run the 52 source-derived cases once. The default
Guardrail Lab suite runs all 76 cases once. Campaign mode is a separate
budget-limited scheduler and may not reach every selected case. Benchmark
metrics, Guardrail Lab outcomes, synthetic demonstrations, and human-confirmed
findings remain separate evidence types.


## Bounded adversarial research mode

The Guardrail Lab CLI exposes `--research-mode` as a convenience switch for
authorized adversarial evaluations. It selects campaign execution, all six
fixed reviewed framings, and evidence-triggered follow-ups within the configured
request budget and time limit. It can be combined with `--case` and
`--source-corpus` to select the target evaluation set.

The mode is intentionally a bounded evaluator rather than an unconstrained
prompt optimizer. Follow-ups use the lab's reviewed framings and are gated by
exact harmless canary signals. Model responses are retained as evidence and
are never executed as tool instructions. Candidate registry entries remain
unverified until a reviewer examines the transcript and repeatability evidence.

For any candidate finding:

1. Confirm that the target and account were explicitly authorized.
2. Inspect the complete request/response transcript and source provenance.
3. Repeat the same case under documented, comparable settings.
4. Distinguish a canary signal, provider error, incomplete run, and actual
   policy failure; do not infer vulnerability from a marker alone.
5. Record reviewer, model/version, date, run configuration, and evidence hash.

The request budget caps scheduled test requests, not provider-level retries.
Campaign mode may stop before every selected case is reached. Offline CI tests
software behavior only; it is not a live provider evaluation.
