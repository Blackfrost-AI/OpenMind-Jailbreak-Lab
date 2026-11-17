# External prompt-pattern corpus — not part of the active release

This page is retained as historical research context only. The previously
described `EXT-001`–`EXT-015` JSONL dataset is **not present in the current
repository tree**, and the example path
`data/external_prompt_patterns_v1.jsonl` is not a runnable input. Do not use
the old generation command or count those cases as part of the current suite.

The active source-derived corpus is the 52-case safe adaptation set at
`data/source_corpus/safe_adaptations.jsonl` (`GL-SRC-001`–`GL-SRC-052`).
It is based on the user's uploaded archive, keeps source IDs, paths, and
SHA-256 hashes, and rewrites risky material into harmless instruction-boundary
tests with inert canaries. It does not copy or execute original prompt bodies.

Run the active source-derived cases with:

```bash
python -m modules.guardrail_lab --provider gemini --source-corpus \
  --output reports/source-corpus.json
```

See [source-corpus handling](../../data/source_corpus/README.md) and the
[Guardrail Lab README](README.md) for the authoritative inventory, scope, and
execution instructions.
