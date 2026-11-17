# OpenMind Jailbreak Lab — Release Candidate Notes

**Suggested release tag:** `v0.7.0-rc.2`
**Target commit:** the final `main` commit containing this release-notes file
**Release type:** Pre-release candidate

## What changed since v0.7.0-rc.1

- **Original Source Corpus browser (new component, `modules/original_source_corpus/` v0.1.0):** a separate metadata-only browser for the authentic archive — 55 records (source ID, path, size, SHA-256, status), 0 executable. Search by source ID, path, or status; exact record lookup; archive SHA-256 verification against the manifest; blank human-review template generation. The archive itself is not in the repo; original prompt bodies are never copied or executed.
- **Corpus loader hardening (reviewed and fixed after rc.1):** unknown source IDs now error (exit 2) instead of silently returning zero matches; strict field validation (non-empty strings, non-negative integer byte counts, 64 lowercase hex SHA-256); non-object JSONL lines (`[]`, `null`, `"text"`, numbers, booleans) rejected with a line-numbered error instead of an uncaught AttributeError; inventory and manifest paths resolved from the module location so `--verify-archive` works outside the repository root; manifest placeholder count corrected (`empty_file_count` 0, `one_byte_placeholder_count` 1).
- **Manual review workspace (new):** `manual_reviews/` with the adjudication workflow, a structured JSON template, and per-case review records. The checked-in source review template is regression-tested against the generator so the example and CLI output cannot drift apart.
- **Repository hygiene:** `main` is now protected by a ruleset against branch deletion and force-pushes. Direct pushes still work; there is no pull-request requirement.
- **Docs:** the Hugging Face Space link now reads "Space" (not "demo"); source-corpus validation and review-template hardening documented in the module, corpus, and root READMEs.

## Verification

The [Validate benchmark run 44165854106](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/44165854106) passed on commit `5ac4cc4` on Python 3.10, 3.11, and 3.12. The validation workflow compiled all Python sources, validated all benchmark versions, ran the quality audit and module smoke tests (including the new corpus browser smoke test), and executed the complete unit-test suite (334 tests). The [Provider adapter regression matrix run 44164686055](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/44164686055) passed on commit `ea23356`, which contains all Python changes in this release; commits after it are documentation-only. The full unit-test suite (334 tests) and benchmark validation were also run locally on the release commit and passed.

The 76-case live provider suite and selectable multi-provider Actions workflow have not been live-executed as part of this offline CI verification.

## Known limitations

- The current benchmark has 66 cases: 38 adversarial and 28 benign.
- All benign controls currently share the `benign_utility` family.
- Three adversarial families currently have one case each: `history_edit`, `cross_model_pipeline`, and `hypothetical_framing`.
- Live cross-provider comparisons against Gemini, Claude, and OpenAI remain outstanding.
- Full-suite GitHub Actions runs can send 52 or 76 live requests depending on selected scope and may incur provider charges; no live model results are implied by CI.
- A green workflow validates software paths; it does not prove a jailbreak, certify a model, or establish universal security.

## Before publishing this candidate

1. Tag the final `main` commit containing this release-notes file.
2. Create the tag `v0.7.0-rc.2` at that commit.
3. Publish as a GitHub **pre-release**, not a stable v1.0 release.
4. Keep live model findings separate from offline CI results.
