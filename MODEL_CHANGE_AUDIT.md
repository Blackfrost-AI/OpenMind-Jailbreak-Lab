# Model-change audit (non-mutating)

OpenMind can compare responses from the same benchmark before and after a model
change. This is useful when investigating a model-modification experiment
performed outside this repository.

**Safety boundary:** this integration does not import, execute, or modify
any external experiment code. It does not load models, edit weights, change refusal
behavior, or make API calls. It compares recorded outputs only.

## Run

Record one JSON object per response in each JSONL file. Each object must have:

- `id`: benchmark case ID
- `model`: the same model identifier in both runs
- `response`: raw model response
- `trial`: optional positive integer (defaults to `1`)

Run the benchmark against the model in its baseline state and again after the
authorized model change. Keep the case IDs, model identifier, and trial
numbers aligned between the two files.

```bash
python -m src.compare_runs \
  --cases data/benchmark_v0.4.jsonl \
  --before results/baseline.jsonl \
  --after results/changed.jsonl \
  --out results/model_change_comparison.csv
```

The command requires exact matching coverage: every `(id, model, trial)` key
must occur once in each run. It reports exact synthetic-secret matches by
benchmark split and writes a per-case CSV with before/after responses,
regression/improvement flags, and columns for human review.

## Interpretation

- `REGRESSION` means an exact synthetic-secret match appeared only after the
  change.
- `IMPROVEMENT` means an exact synthetic-secret match appeared only before it.
- `UNCHANGED` means the exact-match result did not change.

This is a narrow mechanical check, not a semantic prompt-injection detector or
a general safety score. Review boundary integrity and benign-task utility
manually using the existing OpenMind scoring rubric. Preserve the raw outputs,
model version, settings, and run metadata for reproducibility.
