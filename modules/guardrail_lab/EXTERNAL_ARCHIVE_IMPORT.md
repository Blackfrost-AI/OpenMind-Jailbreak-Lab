# Uploaded source archive and safe adaptations

The uploaded archive is represented by a metadata-only inventory at [data/source_corpus](../../data/source_corpus/) and a separate set of safe, source-attributed adaptations. This page documents the distinction. It does not import original source files as executable jailbreak prompts.

## Committed files

- `data/source_corpus/source_inventory.jsonl`: 55 metadata records, one for each non-directory file in the uploaded ZIP. All raw inventory records are non-runnable.
- `data/source_corpus/safe_adaptations.jsonl`: 52 safe, runnable test adaptations (GL-SRC-001–GL-SRC-052).
- `data/source_corpus/manifest.json`: source archive SHA-256, record counts, and inventory SHA-256.
- `data/source_corpus/README.md`: inclusion, execution, and handling rules.

## Source integrity

The exact uploaded archive `jailbreaks-main (1)(1).zip` has SHA-256:

`4f76bac118fc58eecfe79497a3f7ce42803c222caba665a72d290d41f6824918`

It contains 55 logical files: 54 non-empty files and one one-byte placeholder treated as empty content. The withdrawn security-quarantine notice `0x8D jailbreaks/grok-fast-v2.md` remains excluded and must not be restored or used. The README and one-byte placeholder are also not adapted.

## Adaptation and execution boundary

The 52 adaptations preserve high-level testable patterns while replacing operational payloads with inert synthetic markers. They are **not verbatim source prompts**. No original prompt bodies are redistributed or executed; no tool actions, real-secret retrieval, malware, destructive operations, or unauthorized access are part of the test cases.

At import time, Guardrail Lab validates the adaptation schema, unique IDs and canaries, safe framing, and source ID/path/SHA-256 match against the inventory. Result JSON records include `source_provenance` so each case can be traced back to the metadata record. The inventory itself remains non-runnable.

Hashes establish byte integrity only; they do not establish licensing, safety, ownership, effectiveness, or model vulnerability. See [the source-corpus README](../../data/source_corpus/README.md) for run commands and exact handling counts.
