# OpenMind Jailbreak Lab v0.2

A small, reproducible, safety-bounded benchmark for instruction-hierarchy and untrusted-content robustness.

## Contents
- `data/benchmark_v0.2.jsonl`: 24 synthetic cases across 8 families.
- `data/schema.json`: JSON Schema for records.
- `src/scoring.py`: transparent human-review scoring.
- `src/evaluate.py`: JSONL validation and score aggregation.
- `SCORING.md`: rubric and outcome rules.
- `RESEARCH_PLAN.md`: experiment protocol and novelty criteria.
- `EXPERIMENT_LOG_TEMPLATE.csv`: run logging template.

## Run locally
From this directory:
```bash
python src/evaluate.py --validate data/benchmark_v0.2.jsonl
```
To summarize a reviewer CSV with columns `family,hierarchy,boundary,utility,calibration`:
```bash
PYTHONPATH=src python src/evaluate.py --scores path/to/reviews.csv
```

## Important limitations
This is a 24-case seed benchmark, not a statistically validated evaluation and not proof of novel jailbreak techniques. The prompts are intentionally benign. Do not use the suite to pursue harmful outputs or unauthorized access.
