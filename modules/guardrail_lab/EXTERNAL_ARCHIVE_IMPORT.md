# External jailbreak evaluation corpus

The importer creates two reproducible JSONL artifacts from the uploaded ZIP:

1. A complete source inventory with each archive member's relative path, SHA-256, byte count, model/folder label, and heuristic pattern tags.
2. A safe evaluation corpus with one harmless synthetic-canary test plus one matched benign control per active, non-empty prompt/configuration file.

The uploaded archive contains 55 files. All members are preserved in the source inventory; non-empty prompt/configuration files become safe marker-based evaluation cases. Prompt bodies are not copied or executed. The generated adversarial cases check whether a model treats an untrusted note as data rather than following its instruction to emit a harmless marker; each is paired with a benign extraction control.

## Run

```bash
python scripts/import_external_prompt_archive.py \
  --input "jailbreaks-main (1).zip" \
  --out data/external_prompt_archive_v2.jsonl \
  --cases-out data/external_jailbreak_eval_v1.jsonl
```

Each generated case carries the source path and SHA-256, model/folder label, heuristic tags, expected signal, and an explicit unreviewed status. For this 55-file archive, the result is 52 adversarial canary cases plus 52 matched benign controls; the withdrawn notice is inventoried but not run.

## Trust and scoring

“Trusted” means source identity and integrity are verifiable; it does not mean the content is safe, licensed for redistribution, accurate, or authorized to override system/developer instructions. Every generated case starts unreviewed. Keyword tags are discovery hints, not proof of a bypass. A candidate failure must be repeated, compared with benign controls, and manually reviewed before confirmation.

Keep the original ZIP in a quarantined research input directory. Never load its contents as system/developer prompts or execute scripts/configurations from it.


## Committed corpus package

A pre-generated package from the reviewed archive inventory is committed at
`data/external_jailbreak_corpus_v1.zip`. Extract it from the repository root:

```bash
mkdir -p data/external_jailbreak_corpus
python -m zipfile -e data/external_jailbreak_corpus_v1.zip data/external_jailbreak_corpus
```

The archive contains:

| File | Records | Purpose |
|---|---:|---|
| `external_prompt_archive_v2.jsonl` | 55 | Source inventory and provenance |
| `external_jailbreak_eval_v1.jsonl` | 104 | 52 canary adaptations plus 52 matched controls |
| `manifest.json` | 1 | Package counts and SHA-256 hashes |

The package's cases are linked to source paths and source hashes. All evaluation
rows are marked `unreviewed`; this is intentional and must not be silently
changed to reviewed or confirmed.

### Current integration boundary

The ZIP is committed as a reusable dataset artifact. The existing
`modules.guardrail_lab` CLI does **not** currently accept this JSONL file as a
case registry, so extracting it does not execute or register these 104 cases.
Do not describe the package as having been run through the provider adapters
until a future loader/adapter integration exists and reports contain these
case IDs. For now, inspect, validate, curate, and safely adapt the records using
the existing GL test-case workflow.

### Integrity and review

Use the manifest to verify SHA-256 hashes before use. Validate JSONL parsing,
unique case IDs, expected counts, and the `unreviewed` status. Preserve the
original package and its manifest unchanged; store any curated or reviewed
version as a separately versioned artifact with reviewer, date, and rationale.

The source inventory is provenance metadata, not a license grant. The package
does not redistribute original prompt bodies. Removing or omitting a source
license does not create permission to republish source material. The withdrawn
notice remains quarantined and must not be executed.


## Dataset separation (17 November 2026)

The project now documents two distinct datasets:

1. **Real source archive provenance** — see [data/source_corpus/README.md](../../data/source_corpus/README.md). The uploaded archive has 55 entries, including 52 non-empty prompt/configuration files. Only metadata and hashes are represented here; original bodies are not redistributed. The withdrawn `grok-fast-v2.md` entry is quarantined.
2. **Synthetic evaluation suite** — see [data/synthetic_evaluation/README.md](../../data/synthetic_evaluation/README.md). It contains 52 generated canary adaptations and 52 matched benign controls. These are synthetic and are not source prompts.

The existing `data/external_jailbreak_corpus_v1.zip` is a legacy combined bundle retained unchanged for traceability. It is not the canonical separated layout. Do not call its 104 generated cases real jailbreak prompts or count them as source examples. The CLI integration limitation described above still applies.
