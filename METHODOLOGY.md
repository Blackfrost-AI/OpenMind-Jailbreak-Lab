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
