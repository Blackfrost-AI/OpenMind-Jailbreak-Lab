# Source archive inventory and safe adaptations

This directory separates the original archive's **metadata-only provenance inventory** from the Guardrail Lab's **safe, runnable adaptations**.

## Files

- `source_inventory.jsonl`: 55 metadata records, one per non-directory archive member. No raw archive record is executable.
- `safe_adaptations.jsonl`: 52 independently rewritten, runnable evaluation cases (GL-SRC-001–GL-SRC-052). Each case records its source ID, original relative path, and source SHA-256.
- `manifest.json`: source archive SHA-256, record counts, and inventory SHA-256.

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

At import time, Guardrail Lab validates each adaptation's schema, unique IDs/canaries, safe framing, source ID, source path, and SHA-256 against `source_inventory.jsonl`. Live result records include the matching source provenance. The inventory and adaptations do not establish licensing, safety of the original source, or model vulnerability.

Run the source-derived cases with:

```bash
python -m modules.guardrail_lab --provider gemini --source-corpus --output reports/source-corpus.json
```

The default suite runs all 76 cases (24 core plus 52 source-derived). A bounded campaign is limited by its configured request budget and may not reach every selected case.
