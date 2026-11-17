# OpenMind Jailbreak Lab

<p align="center">
  <img src="assets/logo.jpg" alt="OpenMind Jailbreak Lab logo" width="420">
</p>

<p align="center"><strong>AI security research lab for testing prompt injection, identifying vulnerabilities, and evaluating AI guardrails.</strong></p>

OpenMind is a provider-neutral toolkit for **authorized, repeatable AI security evaluation**. It combines bounded guardrail tests, adversarial research workflows, a benchmark, a provider-backed scanner, and evidence reports.

It is an assessment tool—not a promise of successful jailbreaks. A completed run means tests executed and evidence was collected; it does not prove a vulnerability.

## Start here

- **[Start Here](START_HERE.md)** — quickest setup, including GitHub Actions and mobile use.
- **[Installation](INSTALLATION.md)** — local setup, credentials, providers, and advanced options.
- **[Guardrail Lab guide](modules/guardrail_lab/README.md)** — test cases, campaigns, and reports.

## What is included

### Guardrail Lab

Runs individual cases or bounded campaigns against supported hosted APIs and compatible local inference servers.

- **76 runnable cases:** 24 core cases and 52 source-derived safe adaptations.
- Fixed, reviewable campaign framings and request/time limits.
- Provider adapters, JSON evidence reports, and a findings registry.
- Manual review for ambiguous or potentially concerning results.

The optional `--research-mode` selects six reviewed framings and enables evidence-triggered follow-ups within the configured request budget. It supports authorized testing and evidence collection; it does not generate unrestricted harmful bypasses or execute model-generated tool instructions.

Generate a local review set without API calls:

```bash
python -m modules.guardrail_lab.discovery \
  --input data/discovery_seed_cases.example.jsonl \
  --variants 6 --seed 17 --out results/discovery_cases.jsonl
```

Run a bounded Gemini research campaign:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
python -m modules.guardrail_lab --provider gemini --research-mode \
  --source-corpus --budget 100 \
  --output reports/gemini-research.json \
  --registry findings/registry.jsonl
```

The 52 source-derived cases preserve source IDs, paths, and hashes, but replace risky instructions with inert markers; they are **not verbatim source prompts**. The raw archive inventory is metadata-only. See [source corpus details](data/source_corpus/README.md).

### Other modules

- **[AI Scanner](modules/ai_scanner/README.md):** provider-backed checks and response evidence.
- **[OpenMind Benchmark](SCORING.md):** versioned JSONL evaluation set. Current tracked file: [benchmark_v0.6.1.jsonl](data/benchmark_v0.6.1.jsonl), 66 cases.
- **[JB-002](modules/jb002/README.md):** records and validates manually observed results.

## Provider coverage

Guardrail Lab supports these adapters:

| Hosted providers | Compatible/local endpoints |
|---|---|
| OpenAI, Anthropic Claude, Google Gemini | OpenAI-compatible APIs |
| DeepSeek, GLM/Zhipu, Moonshot | Ollama, vLLM |
| NVIDIA NIM, OpenRouter, Groq, Together | LM Studio, llama.cpp server, LocalAI |

Availability depends on credentials, model IDs, endpoint support, and provider limits. GitHub Actions tests one selected provider/model per invocation; it does not automatically enumerate every model.

## Quick start

Requires Python 3.10+ and Git. Clone the repository:

```bash
git clone https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab.git
cd OpenMind-Jailbreak-Lab
```

Run the local checks:

```bash
python -m unittest discover -s tests -v
python -m src.validate
python -m modules.guardrail_lab --list
```

Example provider run:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
python -m modules.guardrail_lab --provider gemini \
  --output reports/gemini.json
```

Use the matching environment variable for your provider. Keep credentials out of source files and commits. See the [provider matrix](modules/guardrail_lab/PROVIDER_MATRIX.md) for configuration details.

## GitHub Actions

The repository includes a manually triggered [multi-provider workflow](.github/workflows/multi-provider-red-team.yml). Add the provider key under **Settings → Secrets and variables → Actions**, then open **Actions → Manual multi-provider Guardrail Lab**.

Choose a provider, exact model ID, scope, and mode:

- `core`: 24 core cases
- `source`: 52 source-derived adaptations
- `all`: all 76 cases
- `full_suite`: one run per selected case
- `campaign`: bounded request budget with up to six reviewed framings

Download the JSON evidence artifact from the workflow run. GitHub-hosted runners cannot reach services bound only to your local machine. API use may incur charges and is subject to provider quotas.

## Reading results

Reports retain case IDs, provider/model metadata, prompts, responses, request errors, and assessment labels where available.

| Label | Meaning |
|---|---|
| `potential_guardrail_failure` | Signal requiring transcript review and reproduction |
| `ambiguous_canary_mention` | Canary appears in a longer response; context matters |
| `boundary_held` | Expected boundary behavior observed |
| `control_passed` | Benign control behaved as expected |
| `manual_review` | Automated assessment is inconclusive |
| `partial_run` | Run did not complete |

A canary quoted in an explanation, translation, or warning is not by itself proof of a bypass. Provider errors, rate limits, proxy blocks, and authentication failures are infrastructure outcomes—not model behavior. Treat candidate signals as unverified until reviewed and reproduced.

## Recent comparison snapshot

The 16 November 2026 evaluation compared four specific model configurations. Benchmark counts below are adjudicated findings; blocked and no-text cases were unscored, not passes.

| Tested configuration | Benchmark findings |
|---|---:|
| GPT-5.6-sol (AgentRouter) | 1 / 64 answered |
| Claude Haiku 5.5 (Qronos) | 2 / 63 answered |
| Gemini 3.5 Flash Lite | 7 / 66 |
| NVIDIA Nemotron 3 Nano Omni | 9 / 61 text-bearing |

The benchmark, Guardrail Lab, and AI Scanner are separate instruments and must not be combined into one score. Results describe only the tested configurations and gateways, not universal model security. See [methodology](METHODOLOGY.md), [scoring](SCORING.md), and the dated evidence report before drawing conclusions.

## Responsible testing

- Test only systems you own or have explicit permission to assess.
- Follow provider terms, rate limits, and applicable law.
- Use synthetic canaries and non-sensitive test data.
- Do not seek real credentials, private user data, or hidden secrets.
- Keep API keys in environment variables or Actions secrets.
- Review reports before sharing; transcripts may contain sensitive details.
- Reproduce findings and use responsible disclosure.

If a key is exposed, revoke it and create a replacement.

## Documentation

- [Installation and setup](INSTALLATION.md)
- [Guardrail Lab](modules/guardrail_lab/README.md)
- [Provider matrix](modules/guardrail_lab/PROVIDER_MATRIX.md)
- [Discovery engine](modules/guardrail_lab/DISCOVERY_ENGINE.md)
- [Registry and evidence handling](modules/guardrail_lab/REGISTRY.md)
- [External archive import](modules/guardrail_lab/EXTERNAL_ARCHIVE_IMPORT.md)
- [AI Scanner](modules/ai_scanner/README.md)
- [JB-002](modules/jb002/README.md)
- [Methodology](METHODOLOGY.md)
- [Release checklist](RELEASE_CHECKLIST.md)
- [Release status](RELEASE_STATUS.md)

## Quality checks

```bash
python -m src.quality_audit data/benchmark_v0.6.1.jsonl
python -m modules.guardrail_lab.compare \
  reports/gemini.json reports/openai.json \
  --output reports/comparison.json
```

The quality audit checks duplicates, family coverage, split overlap, and synthetic-secret handling. The comparison tool reports shared coverage and label disagreements; neither replaces manual transcript review.

For a no-network demonstration, run `python -m modules.guardrail_lab.demo --output reports/synthetic-demo.json`. The output is explicitly labelled fictional and is not evidence of a live model finding.

## Project status and license

OpenMind is an evolving research toolkit. Provider behavior and model availability change; not every combination has been independently live-tested. Results are experimental evidence, not certification. See [RELEASE_STATUS.md](RELEASE_STATUS.md) for verified CI results and remaining release gates, and [LICENSE](LICENSE) for licensing terms.
