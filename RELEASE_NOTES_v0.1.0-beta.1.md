# OpenMind Jailbreak Lab v0.1.0-beta.1

**Release type:** Pre-release  
**Target commit:** `67ec0bf89ffecddc1d604ee40e647de93c059b4b` (this tag)  
**Status:** Public source repository; pre-release candidate, not a production certification.

## Highlights

- Provider-neutral evaluation framework with adapters for OpenAI, Anthropic Claude, Google Gemini, and compatible endpoints.
- Bounded Guardrail Lab campaign with 24 reviewed case-based tests.
- Versioned 66-case benchmark (`data/benchmark_v0.6.1.jsonl`): 38 adversarial and 28 benign controls.
- Non-destructive benchmark quality audit and cross-report comparison.
- Structured evidence reports, conservative outcome labels, and SHA-256 record integrity checks.
- GitHub Actions workflows for benchmark validation and offline provider-adapter regression testing.

## Verification

**Tag target vs. verified commit:** this release is tagged at `67ec0bf`, whose only change over its parent `fe70526` is this release-notes file. The benchmark validation workflow ran on `fe70526`:

- [Validate benchmark — run 43946290403](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/43946290403)

It also ran on the tagged commit `67ec0bf` and passed:

- [Validate benchmark — run 43946486407](https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab/actions/runs/43946486407)

The provider-adapter regression matrix has passed on earlier commits, but no provider-matrix workflow run exists for this tagged commit — that workflow runs only on pull requests touching provider files, not on pushes to main. Do not interpret offline tests as live provider certification.

## Known limitations

- The benchmark quality audit reports that benign controls currently occupy one family (`benign_utility`) and three adversarial families are singletons (`history_edit`, `cross_model_pipeline`, and `hypothetical_framing`).
- Live Claude and OpenAI comparisons against the same frozen benchmark remain outstanding. Gemini campaign evidence is separate and must not be generalized to other models.
- Provider compatibility does not mean every model/version has been live-tested.
- Ambiguous mentions, refusals, classifier flags, and API errors are not confirmed jailbreaks.
- Findings require raw evidence, repeatability checks, and human review.

## Installation

See [START_HERE.md](START_HERE.md) for the quickest setup and [INSTALLATION.md](INSTALLATION.md) for local installation and provider configuration.

## Responsible use

Use only on systems and accounts for which you have authorization. Use synthetic canaries, avoid real secrets or private data, and do not use the lab to access, extract, or disclose information without permission.

This is a beta evaluation release. It is not a guarantee of successful bypasses, a security certification, or a claim that any provider is universally vulnerable or secure.
