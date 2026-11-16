# OpenMind Jailbreak Lab — Release Candidate Notes

**Suggested release tag:** `v0.7.0-rc.1`  
**Target commit:** the final `main` commit containing this release-notes file  
**Release type:** Pre-release candidate

## Included

- Provider-neutral Guardrail Lab runner and provider adapters.
- Structured provider error reporting and report schema 1.3.
- Per-case evidence SHA-256 checksums.
- Benchmark quality audit for duplicate IDs/prompts, family distribution, and synthetic-secret placement.
- Cross-provider report comparison by case ID.
- CI validation on Python 3.10, 3.11, and 3.12.
- Installation, troubleshooting, methodology, and release-readiness documentation.

## Verification

The validation workflow passed on target commit `b07d398` (Python 3.10, 3.11, 3.12), including benchmark validation, benchmark quality audit, module smoke tests, and unit tests.

The provider adapter regression matrix passed on commit `c8d71b6` (Python 3.10, 3.11, 3.12). Later commits in this candidate changed documentation only.

## Known limitations

- The current benchmark has 66 cases: 38 adversarial and 28 benign.
- All benign controls currently share the `benign_utility` family.
- Three adversarial families currently have one case each: `history_edit`, `cross_model_pipeline`, and `hypothetical_framing`.
- Live cross-provider comparisons against Gemini, Claude, and OpenAI remain outstanding.
- A green workflow validates software paths; it does not prove a jailbreak, certify a model, or establish universal security.

## Before publishing this candidate

1. Tag the final `main` commit containing this release-notes file.
2. Create the tag `v0.7.0-rc.1` at that commit.
3. Publish as a GitHub **pre-release**, not a stable v1.0 release.
4. Keep live model findings separate from offline CI results.
