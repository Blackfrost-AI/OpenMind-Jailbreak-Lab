# OpenMind Jailbreak Lab — Installation Guide

This guide explains how to install, configure, verify, and run OpenMind Jailbreak Lab.

OpenMind is an AI security research toolkit for authorized testing of instruction-boundary weaknesses, prompt-injection defenses, guardrail behavior, and model vulnerabilities.

---

## 1. Requirements

Before installing, make sure you have:

* Python 3.10 or newer.
* Git.
* Internet access for cloning and hosted API providers.
* An API key for any hosted provider you intend to test.
* A local inference server if testing locally hosted models.

Dependencies: The repository's core modules use Python's standard library. No separate pip install step is currently required.

Python 3.12 is used in CI.

Verify Python

Linux / macOS:

```bash
python3 --version
```

Windows:

```powershell
py --version
```

---

## 2. Download the repository

Clone the repository:

```bash
git clone https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab.git
```

Enter the project directory:

```bash
cd OpenMind-Jailbreak-Lab
```

Confirm that you are in the repository root:

```bash
ls
```

On Windows:

```powershell
dir
```

You should see directories such as:

* modules/
* src/
* tests/
* data/
* records/

---

## 3. Create a virtual environment (recommended)

A virtual environment keeps the project isolated from other Python installations.

Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can run Python directly through:

```powershell
.venv\Scripts\python.exe --version
```

Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Verify the environment:

```bash
python --version
```

No additional packages need to be installed for the current standard-library implementation.

---

## 4. Verify the installation

Run the following commands from the repository root.

Run unit tests

```bash
python -m unittest discover -s tests -v
```

Validate benchmark data

```bash
python -m src.validate
```

The validator should report:

```
VALIDATION PASSED
```

The current benchmark contains 66 cases.

List Guardrail Lab tests

```bash
python -m modules.guardrail_lab --list
```

List JB-002 tests

```bash
python -m modules.jb002 list
```

These listing commands do not require API credentials or make provider API calls.

---

## 5. Configure API credentials

API keys must be supplied through environment variables.

Never place credentials directly into Python files, source code, reports, or Git commits.

OpenAI

Variable:

```
OPENAI_API_KEY
```

Linux / macOS:

```bash
export OPENAI_API_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
```

Anthropic Claude

Variable:

```
ANTHROPIC_API_KEY
```

Linux / macOS:

```bash
export ANTHROPIC_API_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:ANTHROPIC_API_KEY="YOUR_API_KEY"
```

Google Gemini

Supported environment variables:

```
GEMINI_API_KEY
GOOGLE_API_KEY
```

Linux / macOS:

```bash
export GEMINI_API_KEY="YOUR_API_KEY"
```

Windows PowerShell:

```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

Use the provider's own documentation to confirm current model availability and account limits.

---

## 6. Supported AI providers

Native provider integrations

The AI Scanner supports:

* OpenAI
* Anthropic Claude
* Google Gemini

Example commands:

```bash
python -m modules.ai_scanner --provider openai
python -m modules.ai_scanner --provider anthropic
python -m modules.ai_scanner --provider gemini
```

OpenAI-compatible providers

Guardrail Lab also supports OpenAI-compatible chat-completions endpoints.

This allows testing compatible hosted gateways and self-hosted open-source models.

Supported local server presets include:

| Provider | Default endpoint |
|---|---|
| Ollama | localhost:11434/v1 |
| vLLM | localhost:8000/v1 |
| LM Studio | localhost:1234/v1 |
| llama.cpp | localhost:8080/v1 |
| LocalAI | localhost:8080/v1 |

Examples:

Ollama

```bash
python -m modules.guardrail_lab \
  --provider ollama \
  --model llama3.1
```

vLLM

```bash
python -m modules.guardrail_lab \
  --provider vllm \
  --model meta-llama/Llama-3.1-8B-Instruct
```

LM Studio

```bash
python -m modules.guardrail_lab \
  --provider lm-studio \
  --model your-loaded-model
```

llama.cpp

```bash
python -m modules.guardrail_lab \
  --provider llama-cpp \
  --model your-model
```

LocalAI

```bash
python -m modules.guardrail_lab \
  --provider localai \
  --model your-model
```

Start the relevant inference server and load the model before running tests.

Local server presets do not install models or start inference servers automatically.

---

## 7. Configure custom providers

For hosted providers or custom OpenAI-compatible gateways:

```bash
export OPENMIND_COMPAT_KEY="YOUR_API_KEY"
```

Then run:

```bash
python -m modules.guardrail_lab \
  --provider openai-compatible \
  --base-url "https://YOUR-PROVIDER.example/v1" \
  --api-key-env OPENMIND_COMPAT_KEY \
  --model "YOUR-MODEL"
```

You can also configure:

```
OPENAI_COMPAT_BASE_URL
OPENAI_COMPAT_MODEL
```

The compatible adapter uses its configured default API-key environment variable unless overridden with --api-key-env.

Local servers may not require an API key.

Security requirements:

* HTTPS is required for remote endpoints.
* HTTP is permitted for supported loopback endpoints.
* Do not embed credentials in endpoint URLs.
* Never publish API keys in reports or commits.

Not every OpenAI-compatible service implements the same features. Compatibility depends on the endpoint's chat-completions implementation.

---

## 8. Run your first AI Scanner test

Example using Gemini:

```bash
python -m modules.ai_scanner \
  --provider gemini \
  --output reports/gemini.json
```

Example using OpenAI:

```bash
python -m modules.ai_scanner \
  --provider openai \
  --output reports/openai.json
```

Example using Claude:

```bash
python -m modules.ai_scanner \
  --provider anthropic \
  --output reports/claude.json
```

Reports are written to the paths specified by --output.

---

## 9. Run Guardrail Lab

Run the default test suite:

```bash
python -m modules.guardrail_lab \
  --provider gemini \
  --output reports/gemini-guardrail.json
```

Run selected cases:

```bash
python -m modules.guardrail_lab \
  --provider openai \
  --case GL-001 \
  --case GL-004 \
  --output reports/selected-cases.json
```

Run a bounded automated campaign

```bash
python -m modules.guardrail_lab \
  --provider openai \
  --campaign \
  --budget 36 \
  --variants 3 \
  --delay 1 \
  --max-seconds 600 \
  --output reports/openai-campaign.json
```

Campaign options:

| Option | Description |
|---|---|
| --campaign | Enables bounded automated testing |
| --budget | Maximum number of test requests (1–1000; default 36) |
| --variants | Number of fixed follow-up framings (1–6; default 3) |
| --delay | Delay between requests |
| --max-seconds | Campaign scheduling time limit |
| --case | Select specific test cases |
| --output | Report destination |

Campaigns use a fixed variation library and configured request limits.

They are not unrestricted prompt-generation systems.

---

## 10. Review reports

Reports use JSON format.

They contain information such as:

* Provider and model information.
* Test case identifiers.
* Prompts and responses.
* Potential failure indicators.
* Request errors.
* Assessment results.
* Available request metadata.

Important result classifications include:

| Result | Meaning |
|---|---|
| potential_guardrail_failure | Canary detected; requires manual review |
| boundary_held | Expected boundary behavior observed |
| control_passed | Benign control behaved as expected |
| manual_review | Human assessment required |
| partial_run | Test did not complete fully |

A potential failure is not automatically a confirmed vulnerability.

Reproduce findings and inspect the complete request and response before reporting a security issue.

Reports may contain sensitive testing information. Review them before sharing publicly.

---

## 11. Troubleshooting

Python command not found

Try:

```bash
python3 --version
```

On Windows:

```powershell
py --version
```

Install Python 3.10 or newer if necessary.

Module not found

Make sure you are running commands from the repository root:

```bash
cd OpenMind-Jailbreak-Lab
```

API authentication failure

Check that:

* The correct API key is configured.
* The environment variable matches the provider.
* The key has not expired.
* Your provider account has API access.

Rate-limit errors

Reduce request frequency with:

```
--delay 5
```

Check your provider's current rate limits before increasing campaign budgets.

Local model connection failure

Check that:

* Your inference server is running.
* The model is loaded.
* The configured port is correct.
* The endpoint supports /v1/chat/completions.
* The model name matches the server's loaded model.

Benchmark validation failure

Run:

```bash
python -m src.validate
```

Inspect the reported file and record identifiers. Do not manually modify benchmark records just to suppress validation errors.

Unit-test failure

Run:

```bash
python -m unittest discover -s tests -v
```

Review the failing test and traceback before changing project files.

---

## 12. Security and responsible use

OpenMind is intended for authorized AI security research and defensive testing.

Only test systems you own or have explicit permission to assess.

* Respect provider terms and rate limits.
* Do not target unauthorized third-party services.
* Do not attempt to retrieve real secrets or private information.
* Protect API credentials and generated reports.
* Manually reproduce and review suspected vulnerabilities.
* Follow responsible disclosure procedures.

A successful test run does not constitute a security certification or prove that a model is secure.

---

## 13. Additional documentation

For further information, consult:

* [Main README](README.md)
* [AI Scanner Documentation](modules/ai_scanner/README.md)
* [Guardrail Lab Documentation](modules/guardrail_lab/README.md)
* [JB-002 Documentation](modules/jb002/README.md)
* [Benchmark Scoring](SCORING.md)
* [Testing Methodology](METHODOLOGY.md)
* [Injection and Guardrail Testing](INJECTION_GUARDRAIL_TESTING.md)

Repository:

https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab

---

OpenMind Jailbreak Lab

Authorized AI security research. Reproducible testing. Evidence-first evaluation.
