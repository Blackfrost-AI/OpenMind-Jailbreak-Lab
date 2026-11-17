# Source archive inventory and safe adaptations

This directory contains two distinct research layers: (1) a metadata-only provenance inventory of the authentic archive, and (2) inert, rewritten adaptations used by the defensive Guardrail Lab.

## Files

- `source_inventory.jsonl`: 55 metadata records, one per non-directory archive member. No raw archive record is executable.
- `safe_adaptations.jsonl`: 52 rewritten, bounded evaluation cases (GL-SRC-001–GL-SRC-052). They are not verbatim originals.
- `manifest.json`: archive SHA-256, record counts, and inventory SHA-256.

## Separation

The independent [Original Source Corpus browser](../../modules/original_source_corpus/README.md) searches and displays provenance metadata without merging originals into the defensive runner. The source archive is identified by SHA-256; its raw prompt bodies are not copied into this public repository. The inventory contains IDs, paths, byte sizes, hashes, and status only.

## Verified source

- Archive SHA-256: `4f76bac118fc58eecfe79497a3f7ce42803c222caba665a72d290d41f6824918`
- Archive members: 55
- Non-empty members: 54 (including the README and withdrawn notice)
- Empty placeholder: 1
- Withdrawn notice: 1 (`0x8D jailbreaks/grok-fast-v2.md`); excluded from runnable use
- Safe adaptations: 52
- Raw source records marked runnable: 0

## Browse and validate

```bash
python -m modules.original_source_corpus
python -m modules.original_source_corpus --search qwen
python -m modules.original_source_corpus --id SRC-005 --json
python -m modules.original_source_corpus --verify-archive /path/to/source_archive.zip
```

The archive verifier compares the supplied file's SHA-256 with `manifest.json`. It does not execute archive content.

The JSONL inventory loader rejects malformed JSON, non-object JSON values (including arrays, strings, numbers, booleans, and null), missing or incorrectly typed fields, invalid hashes, runnable records, and duplicate IDs or paths. Errors identify the affected line or validation rule rather than failing later with an attribute error. The test suite includes regression coverage for these cases.

## Adaptation runner

Only the separate safe adaptations are included in Guardrail Lab's `--source-corpus` option. They replace risky instructions with inert canary markers and validate provenance against this inventory. They do not prove the original source was safe or that any model is vulnerable.

## Human review

Generate a blank review record for one source item:

```bash
python -m modules.original_source_corpus --id SRC-001 \
  --export-review-template manual_reviews/SRC-001.json
```

Review records are separate from run inputs. A review decision never automatically adds raw source text to an execution pipeline.
