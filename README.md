<p align="center">
  <img src="assets/logo.jpg" alt="OpenMind Jailbreak Lab logo" width="480">
</p>

<h1 align="center">OpenMind Jailbreak Lab</h1>

<p align="center">
  <strong>Provider-neutral AI security testing, guardrail evaluation, and evidence-driven red teaming.</strong>
</p>

<p align="center">
  Test carefully. Record evidence. Verify findings.
</p>

---

## Overview

OpenMind Jailbreak Lab is an extensible framework for authorized security evaluation of large language models and AI applications. It brings repeatable prompt-injection tests, instruction-boundary probes, provider adapters, benchmark validation, and structured result collection into one project.

The project has shifted from a Gemini-focused test setup to a **multi-provider evaluation lab**. The same bounded test cases and reporting approach can be used with supported hosted APIs and compatible local inference servers. Provider support is adapter-based: compatibility does not imply that every model or endpoint has been independently live-tested.

**This is a testing and assessment tool, not a promise of successful jailbreaks.** A completed run means requests were executed and evidence was collected. It does not establish that a safeguard was bypassed or that a vulnerability exists.

## Start here

New to the project? Follow the short [Start Here guide](START_HERE.md). It includes the simplest GitHub Actions setup (including running from a phone), the required API secret, how to launch one provider/model, and how to read the evidence report. For local installation and advanced options, use [INSTALLATION.md](INSTALLATION.md).

## What the lab evaluates

- Prompt injection in quoted text, documents, retrieved passages, and simulated tool output
- Instruction hierarchy and untrusted-content boundaries
- False authority claims and role-reassignment attempts
- Encoded and multilingual untrusted content
- Multi-turn consistency and context handling
- Benign control tasks and over-refusal behavior
- Provider adapter behavior, request failures, and response normalization

Tests use bounded scenarios and harmless synthetic canaries. They do not require real secrets, private data, destructive actions, or access to third-party accounts.
Each Guardrail Lab case is evaluated beneath a fixed lab-owned system instruction that explicitly marks quoted text, documents, retrieved passages, metadata, and tool outputs as untrusted. This creates a reproducible system-versus-user trust boundary across supported providers; it is a standardized harness baseline, not a copy of any target application's private system prompt.

## Project modules

### Guardrail Lab

The main API-backed evaluation module. It runs individual cases or bounded campaigns, captures request/response evidence, and assigns conservative result labels for follow-up review.

- 24 case-based tests (GL-001–GL-024)
- Fixed-framing campaign variants and request/time limits
- Provider-specific configuration and compatible endpoints
- JSON evidence reports
- Manual review for ambiguous or potentially concerning results

See [Guardrail Lab documentation](modules/guardrail_lab/README.md), the [provider matrix](modules/guardrail_lab/PROVIDER_MATRIX.md), and the [discovery engine](modules/guardrail_lab/DISCOVERY_ENGINE.md).

### AI Scanner

A separate provider-backed scanner for running supported checks and saving response evidence.

See [AI Scanner documentation](modules/ai_scanner/README.md).

### OpenMind Benchmark

A versioned JSONL benchmark for repeatable evaluation and validation. The current README-tracked benchmark is [benchmark_v0.6.1.jsonl](data/benchmark_v0.6.1.jsonl) (66 cases).

Validate benchmark structure with:

    python -m src.validate

See [scoring](SCORING.md) and [methodology](METHODOLOGY.md).

### JB-002

A small companion module for recording and validating manually observed results.

See [JB-002 documentation](modules/jb002/README.md).

## Provider coverage

The Guardrail Lab includes native adapters and OpenAI-compatible endpoint support.

| Provider / endpoint | Adapter |
|---|---|
| OpenAI | openai |
| Anthropic Claude | anthropic |
| Google Gemini | gemini |
| DeepSeek | deepseek |
| GLM / Zhipu AI | glm |
| Moonshot | moonshot |
| NVIDIA NIM | nvidia |
| OpenRouter | openrouter |
| Groq | groq |
| Together | together |
| Custom OpenAI-compatible API | openai-compatible |
| Ollama | ollama |
| vLLM | vllm |
| LM Studio | lm-studio |
| llama.cpp server | llama-cpp |
| LocalAI | localai |

Provider and model availability depends on the adapter, endpoint implementation, account access, credentials, and current provider limits. Some hosted services require a custom base URL or model identifier. Local inference presets require the relevant server to be running.

The provider-neutral GitHub Actions workflow runs **one selected provider and model per invocation**; it does not automatically enumerate every model offered by a provider.

## Quick start

### Requirements

- Python 3.10 or newer
- Git
- API credentials for the hosted provider being tested, or a reachable local inference endpoint

### Install

    git clone https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab.git
    cd OpenMind-Jailbreak-Lab

No separate pip installation is currently required for the standard-library implementation.

### Verify the checkout

    python -m unittest discover -s tests -v
    python -m src.validate
    python -m modules.guardrail_lab --list

### Configure a provider

Set the appropriate key in your shell; do not paste it into source files or commit it.

Gemini example:

    export GEMINI_API_KEY="YOUR_API_KEY"
    python -m modules.guardrail_lab \
      --provider gemini \
      --output reports/gemini.json

OpenAI example:

    export OPENAI_API_KEY="YOUR_API_KEY"
    python -m modules.guardrail_lab \
      --provider openai \
      --output reports/openai.json

Anthropic example:

    export ANTHROPIC_API_KEY="YOUR_API_KEY"
    python -m modules.guardrail_lab \
      --provider anthropic \
      --output reports/anthropic.json

For other providers and custom endpoints, see [Installation and provider configuration](INSTALLATION.md) and the [provider matrix](modules/guardrail_lab/PROVIDER_MATRIX.md).

## Run the multi-provider GitHub Actions workflow

The repository includes a manually triggered [multi-provider red-team workflow](.github/workflows/multi-provider-red-team.yml).
It runs a bounded campaign of up to 24 requests with up to six fixed, reviewed framings. Adaptive follow-ups require an exact canary-only response; ambiguous mentions are reserved for human review and are not called bypasses.

1. Add the provider credential under **Settings → Secrets and variables → Actions**.
2. Open **Actions → Manual multi-provider red-team suite**.
3. Select the provider adapter and enter the exact model ID supported by your account.
4. Set the request budget and, when applicable, a custom compatible base URL.
5. Start the workflow and inspect its run summary.
6. Download the provider-specific JSON evidence artifact.

The dedicated Gemini full-suite workflow also runs all 24 Guardrail Lab cases with a conservative 13-second request interval. It is manually triggered and requires the `GEMINI_API_KEY` Actions secret. Other provider workflows remain one provider/model per invocation. The workflow supports hosted provider choices and compatible endpoints defined in its dispatch inputs. Localhost-only model servers are not reachable from a GitHub-hosted runner; run those tests from a host that can reach the local server.

A successful workflow indicates that the workflow completed its configured execution and report steps. It is not a successful-bypass indicator. API requests may incur charges and remain subject to provider quotas.

For setup details and credential names, see [INSTALLATION.md](INSTALLATION.md).

## Run a focused trust-boundary test

The four trust-escalation cases, GL-013–GL-016, check whether a model follows harmless instructions embedded in content identified as untrusted.

    python -m modules.guardrail_lab \
      --provider gemini \
      --case GL-013 \
      --case GL-014 \
      --case GL-015 \
      --case GL-016 \
      --output reports/trust-escalation.json

These cases cover an untrusted document, a forged authority claim, encoded content, and a quotation. A canary mentioned as part of an explanation is ambiguous; an exact canary-only response is a potential signal that still requires repeat runs, matched controls, and human review.

## Understanding results

The report records test identifiers, provider/model metadata, prompts, responses, request errors, and assessment outcomes where available.

| Label | Interpretation |
|---|---|
| potential_guardrail_failure | A canary signal was detected; inspect and reproduce before making a finding |
| ambiguous_canary_mention | Canary appears in a longer response; context matters |
| boundary_held | Expected boundary behavior was observed |
| control_passed | A benign control behaved as expected |
| manual_review | Automated assessment is inconclusive |
| partial_run | The run did not complete fully |

A canary appearing in a quote, explanation, translation, or warning is not by itself proof of a bypass. Provider errors, rate limits, proxy blocks, and authentication failures are infrastructure outcomes—not model behavior. Preserve the full transcript and reproduce any suspected issue before reporting it.

## Responsible testing and credential safety

- Test only models, applications, and endpoints you own or have explicit permission to assess.
- Follow provider terms, rate limits, and applicable law.
- Use synthetic canaries and non-sensitive test data.
- Never attempt to obtain real credentials, private user data, or hidden secrets.
- Keep API keys in environment variables or repository Actions secrets; never commit them.
- Review reports before sharing because transcripts may contain sensitive operational details.
- Use responsible disclosure for reproducible security findings.

If an API key has been exposed in chat, logs, or a repository, revoke it and create a replacement.

## Documentation

- [Installation and setup](INSTALLATION.md)
- [Guardrail Lab](modules/guardrail_lab/README.md)
- [Provider matrix and comparison guidance](modules/guardrail_lab/PROVIDER_MATRIX.md)
- [Discovery engine](modules/guardrail_lab/DISCOVERY_ENGINE.md)
- [Adaptive engine](modules/guardrail_lab/ADAPTIVE_ENGINE.md)
- [AI Scanner](modules/ai_scanner/README.md)
- [JB-002](modules/jb002/README.md)
- [Benchmark scoring](SCORING.md)
- [Testing methodology](METHODOLOGY.md)
- [Injection and guardrail testing](INJECTION_GUARDRAIL_TESTING.md)

## Project status

OpenMind is an actively evolving research toolkit. Provider adapters, model identifiers, API behavior, and workflow inputs should be verified against the checked-out revision and the provider's current documentation. Not every provider/model combination has been independently live-tested, and results should be treated as experimental evidence rather than certification.

## License

See [LICENSE](LICENSE) for the repository's license.

---

<p align="center">
  <strong>OpenMind Jailbreak Lab</strong><br>
  Authorized testing · Reproducible evaluation · Evidence-first analysis
</p>

### Synthetic demonstration report

To demonstrate report generation without API credentials or network calls:

```bash
python -m modules.guardrail_lab.demo --output reports/synthetic-demo.json
```

This creates a visibly labelled fictional fixture (`SYNTHETIC_DEMONSTRATION`, zero provider calls, zero confirmed live findings). It is for UI and workflow demonstrations only—not evidence of a real model bypass.


## Quality and release process

See [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) for the reproducible pre-release
checks covering benchmark integrity, provider adapters, report schemas, workflow
validation, and evidence labeling.


## Benchmark quality and provider comparison

Run the non-destructive quality audit against the current benchmark:

```bash
python -m src.quality_audit data/benchmark_v0.6.1.jsonl
```

The audit reports exact/normalized duplicate prompts, family concentration,
singleton adversarial families, split overlap, and synthetic-secret misuse.
Warnings are review prompts, not automatic dataset rejection; errors fail the
command. The current v0.6.1 set has 66 cases (38 adversarial, 28 benign). Its
28 benign controls all use the `benign_utility` family, and several adversarial
families are represented by a single case. These are documented coverage
limitations, not proof that any case is invalid.

Compare saved provider reports using identical case IDs and run settings:

```bash
python -m modules.guardrail_lab.compare reports/gemini.json reports/openai.json --output reports/comparison.json
```

The comparison reports common coverage, missing cases, per-case label
agreement, and disagreements. It compares automated labels only; it does not
rank model security or replace manual review of full transcripts.
