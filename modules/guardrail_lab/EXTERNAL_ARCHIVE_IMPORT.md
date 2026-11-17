# External jailbreak evaluation corpus

The importer creates two reproducible JSONL artifacts from the uploaded ZIP:

1. A complete source inventory with each archive member's relative path, SHA-256, byte count, model/folder label, and heuristic pattern tags.
2. A safe evaluation corpus with one harmless synthetic-canary instruction-boundary test per active, non-empty prompt/configuration file.

The uploaded archive contains 55 files. All members are preserved in the source inventory; non-empty prompt/configuration files become safe marker-based evaluation cases. Prompt bodies are not copied or executed. The generated tests check whether a model treats an untrusted note as data rather than following its instruction to emit a harmless marker.

## Run

```bash
python scripts/import_external_prompt_archive.py \
  --input "jailbreaks-main (1).zip" \
  --out data/external_prompt_archive_v2.jsonl \
  --cases-out data/external_jailbreak_eval_v1.jsonl
```

Each generated case carries the source path and SHA-256, model/folder label, heuristic tags, expected signal, and an explicit unreviewed status.

## Trust and scoring

“Trusted” means source identity and integrity are verifiable; it does not mean the content is safe, licensed for redistribution, accurate, or authorized to override system/developer instructions. Every generated case starts unreviewed. Keyword tags are discovery hints, not proof of a bypass. A candidate failure must be repeated, compared with benign controls, and manually reviewed before confirmation.

Keep the original ZIP in a quarantined research input directory. Never load its contents as system/developer prompts or execute scripts/configurations from it.
