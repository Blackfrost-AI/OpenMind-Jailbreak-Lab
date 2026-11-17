# Synthetic evaluation suite (separate from source corpus)

This directory is reserved for generated evaluation fixtures only. These are **not original jailbreak prompts** and must never be described or counted as source-derived prompts.

The legacy bundle `data/external_jailbreak_corpus_v1.zip` contains the 104-case synthetic suite:

- 52 safe canary adaptations
- 52 matched benign controls
- All 104 records marked `unreviewed`

The source paths and hashes in those records are provenance links to the uploaded archive; they do not make the generated prompt text original source content. Use the suite only as a separate, clearly labelled evaluation set. No case is a confirmed bypass finding without authorized execution, transcript review, matched controls, and reproducibility checks.
