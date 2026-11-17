# Uploaded source archive inventory

The uploaded archive is represented in this repository by a metadata-only inventory at [data/source_corpus](../../data/source_corpus/). This page documents its scope and limitations. It does not provide an importer that turns the source files into executable jailbreak prompts.

## Committed files

- `data/source_corpus/source_inventory.jsonl`: 55 JSONL records, one for each non-directory file in the uploaded ZIP.
- `data/source_corpus/manifest.json`: source archive SHA-256, record counts, and inventory SHA-256.
- `data/source_corpus/README.md`: inclusion and handling rules.

## Source integrity

The exact uploaded archive `jailbreaks-main (1)(1).zip` has SHA-256:

`4f76bac118fc58eecfe79497a3f7ce42803c222caba665a72d290d41f6824918`

It contains 55 logical files: 54 non-empty files and one one-byte placeholder treated as empty content. One file is a withdrawn security-quarantine notice: `0x8D jailbreaks/grok-fast-v2.md`. The notice remains excluded and must not be restored or used.

## Execution boundary

No original prompt bodies are redistributed in this repository. The inventory records provenance and byte integrity only. It contains zero runnable records and is not a jailbreak prompt corpus. Hashes do not establish licensing, safety, ownership, or effectiveness.

Use the versioned benchmark and the registered Guardrail Lab test cases for authorized evaluation. Do not load untrusted archive files as system/developer instructions or execute their scripts/configurations.
