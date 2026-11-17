# Source archive inventory and safe adaptations

This directory separates the original archive's **metadata-only provenance inventory** from the Guardrail Lab's **safe, runnable adaptations**.

## Files

- `source_inventory.jsonl`: 55 metadata records, one per non-directory archive member. No raw archive record is executable.
- `safe_adaptations.jsonl`: 52 independently rewritten, runnable evaluation cases (GL-SRC-001–GL-SRC-052). Each case records its source ID, original relative path, and source SHA-256.
- `manifest.json`: source archive SHA-256, record counts, and inventory SHA-256.
- `variant` field on each adaptation: the injection surface the prompt presents (see “Factorial assignment” below).

## Verified source

- Archive: `jailbreaks-main (1)(1).zip`
- Archive SHA-256: `4f76bac118fc58eecfe79497a3f7ce42803c222caba665a72d290d41f6824918`
- Archive members: 55
- Non-empty files: 54
- Empty files: 1 (the one-byte placeholder is treated as empty)
- Withdrawn notice: 1 (`0x8D jailbreaks/grok-fast-v2.md`); it remains excluded and must not be restored or used.
- Safe adaptations: 52
- Excluded from adaptation: the withdrawn notice, the one-byte placeholder, and the archive README.
- Raw source records marked runnable: 0

## Execution and provenance boundary

The 52 adaptations preserve high-level testable patterns—authority escalation, boundary narrowing, persona reassignment, and simulated agent/tool authority confusion—while replacing risky instructions with inert `SAFE-MARKER-NNN` canaries. They are **not verbatim copies** of original prompt bodies and do not execute tools, retrieve secrets, or perform external actions.

**Research-purposes-only disclaimer:** these cases and their patterns are published for bounded robustness research and evaluation only. They are inert probes, not exploit instructions, and must not be represented as jailbreak techniques for general use.

## Factorial assignment (category × surface)

The original corpus rendered each category as a single fixed prompt repeated with 13 different canary markers — 4 distinct prompts in total. Research on instruction-boundary behavior shows sensitivity to surface form even at fixed semantics, so each category payload is now paired factorially with 13 distinct injection surfaces, giving 52 pairwise-distinct prompts:

- Categories (4): `authority_override`, `boundary_narrowing`, `persona_reassignment`, `agent_authority_confusion`
- Surfaces (13): quoted note, email body, CSV cell, HTML comment, JSON field, retrieved passage, tool output, document record, code comment, Base64-encoded note, Spanish-language note, Markdown link text, fictional narrator

Case GL-SRC-NNN is assigned category `(NNN-1) mod 4` and surface `(NNN-1) // 4` — a balanced Latin square where every category×surface pair occurs exactly once. The assignment and every prompt are reproducible from `modules/guardrail_lab/source_registry.py` (`scripts/regenerate_source_corpus.py` regenerates the JSONL from it), and the loader validates both at import time.

At import time, Guardrail Lab validates each adaptation's schema, unique IDs/canaries, safe framing, source ID, source path, and SHA-256 against `source_inventory.jsonl`. Live result records include the matching source provenance. The inventory and adaptations do not establish licensing, safety of the original source, or model vulnerability.

Run the source-derived cases with:

```bash
python -m modules.guardrail_lab --provider gemini --source-corpus --output reports/source-corpus.json
```

The default suite runs all 76 cases (24 core plus 52 source-derived). A bounded campaign is limited by its configured request budget and may not reach every selected case.
