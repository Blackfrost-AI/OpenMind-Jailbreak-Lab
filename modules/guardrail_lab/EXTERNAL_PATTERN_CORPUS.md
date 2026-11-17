# External prompt-pattern corpus

This corpus adapts high-level pattern categories documented by
[togg53192-cmd/jailbreaks](https://github.com/togg53192-cmd/jailbreaks) into
**independently authored, harmless test cases** for OpenMind. It does not copy
or install that repository's paste-ready system prompts, persona locks,
workspace policies, or model configurations.

The source collection describes prompt patterns such as instruction-priority
claims, persona framing, task routing, policy replacement, workspace/agent
instructions, and harness-specific configuration. This corpus converts those
themes into untrusted-content boundary tests with synthetic canaries and
benign controls. The cases are data to be submitted to the existing Guardrail
Lab; they are never loaded as system or developer instructions.

## Provenance and licensing

The source repository's GitHub metadata does not declare a license. Accordingly,
this project does not redistribute its prompt text. The cases here are original
test scenarios based on high-level concepts, with source attribution retained
for research traceability. Re-check the source repository's licensing before
considering any verbatim reuse.

## Contents

- 12 adversarial synthetic-canary cases
- 3 benign controls
- Stable case IDs (EXT-001–EXT-015)
- Pattern labels and source provenance on every row

## Generate reviewable variants offline

    python -m modules.guardrail_lab.discovery \
      --input data/external_prompt_patterns_v1.jsonl \
      --variants 6 --seed 17 \
      --out results/external_prompt_patterns_v1.generated.jsonl

This creates 90 variants and makes zero provider calls. Review the generated
cases before any live run. For authorized live testing, use the existing
provider-specific campaign workflow and keep request budgets bounded.

A canary mention is not automatically a failure. Review full transcripts,
distinguish quoted mentions from exact canary-only responses, and reproduce
potential findings before confirmation.
