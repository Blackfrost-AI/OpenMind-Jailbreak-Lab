# Release readiness status

**Status: validated development build; not yet a signed v1.0 release.**

This file records what has been verified on the current repository revision and what remains before a public release claim.

## Verified on 2026-11-17

Repository branch: `main`

Code and workflow verification commit:
`d5a51354f16f988cbab7890cbff6e2a8a7b8eb34`

GitHub Actions results:

| Workflow | Run | Result |
|---|---:|---|
| Validate benchmark | [44129447193](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/44129447193) | Success |
| Provider adapter regression matrix | [44129447206](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/44129447206) | Success |

Both workflows passed on Python 3.10, 3.11, and 3.12. Validation compiled all Python source and test files, validated benchmark versions 0.3 through 0.6.1, ran the benchmark quality audit, smoke-tested JB-002, AI Scanner, and Guardrail Lab, and ran the full unit-test suite. The provider matrix passed its complete offline regression suite on all three Python versions.

## Guardrail Lab source-corpus integration

The Guardrail Lab now contains 76 registered cases: 24 core cases and 52 source-derived safe adaptations (`GL-SRC-001`–`GL-SRC-052`). The raw uploaded archive remains a metadata-only inventory; original prompt bodies are not redistributed or executed.

The adaptation loader validates JSONL structure, safe framing, unique IDs and canaries, the inventory checksum, and every source ID/path/SHA-256 relationship. Per-case evidence reports include `source_provenance`. The CLI supports `--source-corpus`; the multi-provider Actions workflow supports `all` (76), `core` (24), and `source` (52) scopes in `full_suite` or bounded `campaign` mode. The dedicated Gemini full-suite workflow now validates all 76 cases.

The verification above is offline CI, not a live provider run. The updated manual multi-provider workflow and 52/76-case live suites still require an authorized, credentialed dispatch before any live-compatibility claim. Documentation-only commits followed the code-verification commit; the final branch CI runs should be checked before release tagging.

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
