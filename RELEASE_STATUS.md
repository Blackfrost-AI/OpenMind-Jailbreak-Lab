# Release readiness status

**Status: validated development build; not yet a signed v1.0 release.**

This file records what has been verified on the current repository revision and what remains before a public release claim.

## Verified on 2026-11-16

Repository branch: `main`

Validated commit before this status document: `c8d71b69cebdd9acc8fcf007722f2446dd174e33`

GitHub Actions results for that commit:

| Workflow | Run | Result |
|---|---:|---|
| Validate benchmark | [43945377667](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/43945377667) | Success |
| Provider adapter regression matrix | [43945377818](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/43945377818) | Success |

The validation workflow passed on Python 3.10, 3.11, and 3.12. Each job ran benchmark schema validation, the benchmark quality audit, JB-002 and AI Scanner smoke tests, Guardrail Lab listing, and the unit test suite.

The provider adapter regression workflow passed its complete offline unit test suite on Python 3.10, 3.11, and 3.12. These are offline software/contract tests; they are not live tests of every hosted provider or model.

The latest benchmark tracked by the README is `data/benchmark_v0.6.1.jsonl` (66 cases: 38 adversarial and 28 benign). The quality audit found no duplicate normalized prompts. It reports coverage warnings: all benign controls currently share the `benign_utility` family, and three adversarial families are singletons (`history_edit`, `cross_model_pipeline`, and `hypothetical_framing`). These warnings are visible coverage limitations, not automatic validation failures.

## Remaining before v1.0

- [ ] Expand benign controls across multiple meaningful families.
- [ ] Add additional cases for the singleton adversarial families, with observable expected behavior and matched benign controls.
- [ ] Run the same frozen benchmark against at least Gemini, Claude, and OpenAI using authorized accounts; record exact model IDs, run dates, settings, raw evidence, and provider errors.
- [ ] Repeat candidate failures and have a human review ambiguous or potential findings.
- [ ] Confirm action versions and workflow permissions during the final release review.
- [ ] Complete the [release checklist](RELEASE_CHECKLIST.md), record reviewer sign-off, and publish scoped release notes.

## Interpretation and limitations

A green CI run verifies the tested repository code paths and offline fixtures. It does not prove every provider adapter works against a live service, certify a model, or demonstrate a jailbreak. A completed live campaign means its configured requests and evidence collection completed; a potential signal still requires reproduction and review.

Do not combine simulated demo fixtures with live results. Do not count API errors or incomplete cases as model passes. Do not publish secrets or sensitive transcripts in reports.

Until the remaining items are completed, describe this repository as a validated development build, not as a completed v1.0 release or a universal guardrail-bypass tool.
