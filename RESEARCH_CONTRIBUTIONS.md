# Research contributions — Blackfrost (November 2026)

This file documents research contributions made from Blackfrost's DWM
(domain weight modification) research program to OpenMind-Jailbreak-Lab.

**Research-purposes-only disclaimer:** All test material contributed here is
published for bounded robustness research and evaluation only. Every new
prompt is an inert probe built on synthetic canary markers
(`SAFE-MARKER-NNN`, `OM-MARKER-XX`). Nothing here is a jailbreak
technique for general use, an unrestricted bypass, or an instruction set for
production systems. Test material is safe to run against any model.

## 1. Source-corpus diversification (4-category × 13-surface factorial)

Before: the 52 source-derived cases rendered **four fixed prompts**
(4 categories × 13 canary markers each) — the corpus's effective
adversarial diversity was 4 shapes, and nothing flagged it because every
prompt differed by its marker.

After: each category payload is paired factorially with 13 injection
surfaces (quoted note, email, CSV, HTML comment, JSON field, retrieval,
tool output, document record, code comment, Base64, Spanish, Markdown
link, fictional narrator) — a Latin square where every category×surface
pair occurs exactly once: **52 pairwise-distinct prompts**.

Grounding: instruction-boundary behavior is sensitive to surface form even
at fixed semantics (frame/persona sensitivity observed across our DWM
evaluations; XSTest-style surface-form variation as a false-refusal
proxy). A model can hold the boundary on one surface while failing on a
semantically identical payload in another medium — so the corpus now tests
that axis instead of repeating one.

Artifacts:

- `modules/guardrail_lab/source_registry.py` — pure registry (categories,
  surfaces, balanced assignment, prompt rendering)
- `scripts/regenerate_source_corpus.py` — regenerates the JSONL from the
  registry, preserving source provenance and canaries
- `modules/guardrail_lab/source_cases.py` — validates variant, factorial
  assignment, and prompt at import time; pins the adaptations SHA-256 in
  the manifest (tamper-evident, like the inventory)
- Evidence records `source_provenance.variant`

## 2. Benchmark v0.7.0 — filling singleton families

Before: v0.6.1's own quality audit flagged two warnings: three singleton
adversarial families (`history_edit`, `cross_model_pipeline`,
`hypothetical_framing`) and a single benign control family
(`benign_utility`).

After: benchmark v0.7.0 adds six adversarial rows filling those families
(2 each) plus a second benign family (`benign_instruction_following`),
75 rows total (44 adversarial / 31 benign). `quality_audit` now returns
`status: pass` with zero warnings.

All new adversarial rows are inert probes: an edited-message "correction"
carrying an injected instruction, another assistant's output/tool result
presented as the answer, and an in-story instruction inside a fictional
scene — each asking the model to *summarize or extract* while the payload
tries to redirect to an `OM-MARKER-XX` canary. The benign rows are plain
single-word instruction-following controls.

Artifacts:

- `data/benchmark_v0.7.0.jsonl` (built by `scripts/build_benchmark_v0.7.0.py`)
- `data/CHECKSUMS.txt` pins its SHA-256
- `.github/workflows/validate.yml` validates and audits v0.7.0
- Shipped-dataset tests in `tests/test_validate.py` and
  `tests/test_quality_audit.py`

## 3. API-key scrubbing in provider error details

Before: both HTTP adapters embed provider error bodies into exception
messages, which flow into local evidence reports. A hostile or
misconfigured `openai-compatible` endpoint could echo the
`Authorization` (or `x-goog-api-key`) header back inside its error body,
writing the live key into the local evidence report.

After: echoed key material is replaced with `***` before raising — both
the bare token and `Bearer <token>` forms, across all three key-carrying
paths (guardrail adapter, scanner compatible endpoints, hosted provider
headers).

Artifacts:

- `modules/ai_scanner/providers.py` — `_scrub_error_detail()`
- `modules/guardrail_lab/openai_compatible.py` — key replacement in error
  detail
- `tests/test_error_detail_scrubbing.py` — hostile endpoints echoing keys
  in 401/403/400/500 bodies

## Verification

All three contributions pass the full local gate set on 2026-11-17:

- 335 unit tests, all passing
- `src.validate` passes on all six benchmark versions (v0.3–v0.7.0)
- `src.quality_audit data/benchmark_v0.7.0.jsonl` → `pass`, 0 warnings
- Corpus import-time validation passes (factorial assignment, prompt
  match, manifest hash pinning)
- Demo mode and `--list` work; evidence records `source_provenance.variant`
