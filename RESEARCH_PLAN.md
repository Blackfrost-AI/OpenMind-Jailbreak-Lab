# OpenMind v0.2 research plan

## Mission 001
Discover and document reproducible weaknesses in how models distinguish trusted task instructions from untrusted content, using harmless extraction, translation, summarization, and classification tasks.

## Test families
- OM-01 Context Boundary Drift
- OM-02 Authority Signal Confusion
- OM-03 Semantic Reframing
- OM-04 Format Boundary Conflict
- OM-05 Temporal Context Conflict
- OM-06 Cross-Context Contamination
- OM-07 Tool-Output Trust Boundary
- OM-08 Multilingual Instruction Boundary

## Experimental protocol
1. Test only models and accounts you are authorized to use.
2. Keep system/developer prompts, tools, and sampling settings consistent where feasible.
3. Randomize test order and include ordinary benign controls.
4. Repeat each case at least three times when stochasticity applies.
5. Record model/version, timestamp, interface/API, settings, full input/output, and run ID.
6. Have two reviewers independently score at least 20% of outputs.
7. Report per-family results, sample sizes, uncertainty, and limitations.

## Original-case development
For each candidate, write a hypothesis first, construct a harmless synthetic input, define expected behavior before running it, deduplicate against existing cases, and pilot with independent reviewers. A failure is not proof of novelty. Claim novelty only after documented comparison with prior public benchmarks.

## Safety boundary
This project studies instruction-following robustness with benign synthetic content. It excludes credential theft, secret extraction, malware, operational wrongdoing, and attempts to weaken safeguards.
