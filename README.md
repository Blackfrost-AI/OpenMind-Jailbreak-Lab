# OpenMind Jailbreak Lab

An AI security research lab for testing guardrails, prompt-injection defenses, model behavior, and potential vulnerabilities across AI services.

## Modules

### AI Scanner

Runs provider-backed tests against supported AI services and records model responses for security analysis.

### Guardrail Lab

A real API-backed adversarial testing module designed to evaluate:

* Direct instruction override attempts
* Prompt injection in documents and retrieved content
* Simulated tool-output injection
* False authority and role reassignment attempts
* Encoded and multilingual untrusted content
* Multi-turn guardrail consistency
* Confidential-instruction boundary handling
* Benign controls and over-refusal

Tests produce structured JSON evidence containing prompts, responses, provider information, errors, and assessment results.

It also runs bounded automated campaigns (`--campaign`, fixed framings, budget/time limits) and supports OpenAI-compatible endpoints (Ollama, vLLM, LM Studio, llama.cpp, LocalAI) for testing local models.

### Benchmark and JB-002

The repository also includes the OpenMind Benchmark (`data/benchmark_v0.5.jsonl`, 56 cases) and JB-002, a three-case module for recording and validating manually observed test results. See `data/` and `modules/jb002/README.md`.

## Supported Providers

* OpenAI
* Anthropic Claude
* Google Gemini
* Any OpenAI-compatible endpoint (local model servers and hosted providers)

Provider and model availability depends on configured API credentials and supported adapters.

## Design Principles

* Real provider-backed testing where credentials are available
* Reproducible test cases
* Evidence-based findings
* Conservative vulnerability classification
* No treating a single suspicious response as a confirmed exploit
* Defensive research and authorized testing

## Installation

Clone the repository:

```
git clone https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab.git
cd OpenMind-Jailbreak-Lab
```

Follow the installation instructions in each module's README.

## Usage

See the individual module documentation for setup, provider configuration, commands, and report formats.

## Disclaimer

This project is intended for authorized AI security research, defensive testing, and responsible vulnerability assessment. Only test systems you own or have explicit permission to assess.

## License

See the repository's LICENSE file.
