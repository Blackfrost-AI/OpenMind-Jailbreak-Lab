# OpenMind Jailbreak Lab — Release Candidate Notes

**Suggested release tag:** `v0.7.0-rc.1`  
**Target commit:** the final `main` commit containing this release-notes file  
**Release type:** Pre-release candidate

## Included

- Provider-neutral Guardrail Lab runner and provider adapters.
- 52 source-derived safe adaptations, bringing the runnable Guardrail Lab inventory to 76 cases (24 core + 52 source-derived).
- Strict source-adaptation loader checks for JSONL schema, safe framing, unique case/source/canary IDs, inventory checksum, and source ID/path/SHA-256 consistency.
- Source provenance (`source_id`, `source_path`, `source_sha256`) embedded in per-case evidence records.
- `--source-corpus` CLI selection and GitHub Actions scope/mode controls for all/core/source sets and full-suite/campaign execution.
- Gemini full-suite evidence validation updated from 24 to 76 cases.
- Structured provider error reporting and report schema 1.3.
- Per-case evidence SHA-256 checksums.
- Benchmark quality audit for duplicate IDs/prompts, family distribution, and synthetic-secret placement.
- Cross-provider report comparison by case ID.
- CI validation on Python 3.10, 3.11, and 3.12.
- Installation, troubleshooting, methodology, and release-readiness documentation.

## Verification

The source-corpus code and workflow changes were validated on commit `d5a51354f16f988cbab7890cbff6e2a8a7b8eb34`. The [Validate benchmark run](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/44129447193) and [Provider adapter regression matrix](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/44129447206) both passed on Python 3.10, 3.11, and 3.12. The validation workflow compiled all Python sources, validated all benchmark versions, ran the quality audit and module smoke tests, and executed the complete unit-test suite. The provider matrix ran the complete offline regression suite.

The 76-case live provider suite and selectable multi-provider Actions workflow have not been live-executed as part of this offline CI verification. Documentation commits after `d5a5135` do not change the tested Python implementation; final-head CI should be checked before tagging.

## Known limitations

- The current benchmark has 66 cases: 38 adversarial and 28 benign.
- All benign controls currently share the `benign_utility` family.
- Three adversarial families currently have one case each: `history_edit`, `cross_model_pipeline`, and `hypothetical_framing`.
- Live cross-provider comparisons against Gemini, Claude, and OpenAI remain outstanding.
- Full-suite GitHub Actions runs can send 52 or 76 live requests depending on selected scope and may incur provider charges; no live model results are implied by CI.
- A green workflow validates software paths; it does not prove a jailbreak, certify a model, or establish universal security.

## Before publishing this candidate

1. Tag the final `main` commit containing this release-notes file.
2. Create the tag `v0.7.0-rc.1` at that commit.
3. Publish as a GitHub **pre-release**, not a stable v1.0 release.
4. Keep live model findings separate from offline CI results.


## Unreleased — bounded adversarial research mode

- Added the `--research-mode` CLI switch for authorized, bounded campaign
  evaluation using six fixed reviewed framings and evidence-triggered follow-ups.
- Supports the 24 core cases, 52 source-derived safe adaptations, or explicitly
  selected cases; source corpus selection can be combined with `--case`.
- Supports JSON evidence output and an optional unverified findings registry.
- Added regression coverage for research-mode selection and the incompatible
  `--no-adaptive` combination.
- This mode does not generate unrestricted jailbreak payloads, execute
  model-produced tool calls, or establish a vulnerability without human review
  and repeatability checks.
- CI status for this change must be read from the linked GitHub Actions run;
  documentation changes do not imply a green workflow or live-provider test.
