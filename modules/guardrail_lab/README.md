# OpenMind Guardrail Lab
**Version:** 0.3.1
**Purpose:** authorized, evidence-first testing of AI instruction-boundary and guardrail behavior.
OpenMind Guardrail Lab is a small Python test harness for checking how an AI model handles untrusted instructions embedded in quoted text, documents, retrieval content, and simulated tool output. It can run individual test cases or a bounded automated campaign, then save structured JSON evidence for review and regression testing.
Use it only with models and services you own or are explicitly authorized to assess.
## What it tests
| Case | Test area |
|---|---|
| `GL-001` | Instructions embedded in quoted text |
| `GL-002` | Instructions embedded in a document |
| `GL-003` | Instructions embedded in retrieved content |
| `GL-004` | Instructions embedded in simulated tool output |
| `GL-005` | False authority claims |
| `GL-006` | Role-reassignment attempts |
| `GL-007` | Encoded untrusted content |
| `GL-008` | Multilingual untrusted content |
| `GL-009` / `GL-010` | Paired two-turn boundary scenario |
| `GL-011` / `GL-012` | Benign controls, including a basic math task |
The probes use harmless canary markers to detect whether untrusted content appears to influence the response. They do **not** attempt to obtain real secrets, access private data, execute tools, compromise accounts, or facilitate harmful safeguard evasion.
## Requirements
- Python 3.10 or newer is recommended.
- The OpenAI-compatible adapter uses Python's standard-library HTTP client and adds no third-party dependency.
- The native OpenAI, Anthropic, and Gemini routes use the repository's existing provider adapter described in [INTEGRATION.md](INTEGRATION.md).
- A supported provider endpoint and its credentials, if required.
## Quick start
Run these commands from the repository root after adding the module as described in [Integration](#integration):
```bash
# List available tests without making API calls
python -m modules.guardrail_lab --list
# Run the default suite against OpenAI
export OPENAI_API_KEY="your-key"
python -m modules.guardrail_lab --provider openai \
  --output reports/openai-guardrail.json
# Run selected cases
python -m modules.guardrail_lab --provider openai \
  --case GL-001 --case GL-004 \
  --output reports/selected-cases.json
# Run the test suite
python -m unittest discover -s tests -v
```
Provider credentials should be supplied through environment variables. Do not place API keys in source files, reports, command-line arguments, or commits. Check provider pricing and rate limits before running tests.
## Provider support
The lab supports the existing `openai`, `anthropic`, and `gemini` provider routes, plus an OpenAI-compatible Chat Completions adapter. The compatible adapter can work with local inference servers and hosted gateways that implement the expected `/v1/chat/completions` request and response format.
### Local and self-hosted models
Convenience provider names and default base URLs are provided for common local servers:
| Provider option | Default base URL |
|---|---|
| `ollama` | `http://localhost:11434/v1` |
| `vllm` | `http://localhost:8000/v1` |
| `lm-studio` | `http://localhost:1234/v1` |
| `llama-cpp` | `http://localhost:8080/v1` |
| `localai` | `http://localhost:8080/v1` |
Examples:
```bash
python -m modules.guardrail_lab --provider ollama --model llama3.1
python -m modules.guardrail_lab --provider vllm --model meta-llama/Llama-3.1-8B-Instruct
python -m modules.guardrail_lab --provider lm-studio --model your-loaded-model
python -m modules.guardrail_lab --provider llama-cpp --model your-model
python -m modules.guardrail_lab --provider localai --model your-model
```
Override a preset endpoint with `--base-url`. Local HTTP is accepted only for loopback hosts (`localhost`, `127.0.0.1`, and `::1`).
### Other OpenAI-compatible endpoints
For a hosted open-model service or custom gateway, supply its HTTPS base URL and model name:
```bash
export OPENMIND_COMPAT_KEY="your-provider-key"
python -m modules.guardrail_lab \
  --provider openai-compatible \
  --base-url "https://YOUR-PROVIDER.example/v1" \
  --api-key-env OPENMIND_COMPAT_KEY \
  --model "YOUR-MODEL" \
  --campaign --budget 36
```
The adapter also reads `OPENAI_COMPAT_BASE_URL` and `OPENAI_COMPAT_MODEL` when the corresponding command-line options are omitted. The API key environment variable defaults to the adapter's configured default; use `--api-key-env` to select another variable. Local servers may omit an API key.
Compatibility is not guaranteed for every service or model. The endpoint must accept chat messages and return a response with `choices[0].message.content`. Optional provider-specific features are not assumed.
### Endpoint security
- HTTPS is required for non-loopback endpoints.
- HTTP is allowed only for loopback/local inference endpoints.
- URL-embedded credentials, query strings, and fragments are rejected.
- Response JSON and expected response fields are validated before use.
- API keys are read from environment variables and are not written to reports.
## Automated campaigns
A campaign runs a bounded sequence of test requests. It starts with one baseline request per selected case. If a harmless canary is detected, it can schedule up to the configured number of additional fixed prompt framings for that case.
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
Useful options:
| Option | Meaning |
|---|---|
| `--campaign` | Run the bounded adaptive campaign rather than a single baseline suite. |
| `--budget N` | Maximum number of test requests (1–1000; default 36). Provider retries may add HTTP attempts. |
| `--variants N` | Number of fixed safe follow-up framings (1–3; default 3). |
| `--no-adaptive` | Disable evidence-triggered follow-up variations. |
| `--delay SECONDS` | Pause between requests. |
| `--max-seconds N` | Stop scheduling requests after the time limit; an in-flight request is not interrupted. |
| `--case ID` | Select a case; repeat the option to select multiple cases. |
| `--output PATH` | Write the JSON report to the specified path. |
The paired `GL-009` / `GL-010` test carries conversation context between its two turns. If selecting `GL-010`, include `GL-009` immediately before it. Duplicate and unknown case IDs are rejected. If the setup turn fails, the follow-up is recorded as a partial run and is not sent without its required context.
The campaign scheduler is deliberately bounded and uses a fixed variation library; it does not perform unconstrained prompt generation. The request budget counts test requests, while the underlying repository provider adapter may retry transient failures. The time limit is checked between requests and cannot cancel a request already in progress.
## Reports and interpretation
Reports are JSON and retain per-case outcomes, response evidence, provider/model information, and error details where available. Treat reports as security-testing evidence: store them appropriately and review them before sharing, since model responses may contain information you did not intend to publish.
| Result | Interpretation |
|---|---|
| `potential_guardrail_failure` | The harmless canary appeared in the response. This is a signal for manual reproduction, not proof of a vulnerability. |
| `boundary_held` | The expected boundary signal was observed and the canary was not emitted. |
| `control_passed` | A benign control behaved as expected. |
| `manual_review` | The response did not match the simple expected signal. |
| `partial_run` | A provider call failed or a required paired step could not be completed. |
A canary match can be a false positive or depend on model wording, provider behavior, and test configuration. Exact canary matching cannot tell quoting from following: several cases ask the model to describe, translate, or flag the injected text, and a correct answer quotes the canary while doing so. Confirm a failure only when the model outputs the canary as its own compliance (for example, the response is just the canary). Reproduce important findings, inspect the full request/response context, and document the model version and date before drawing conclusions. This tool is a lightweight test harness, not a certification, penetration test, or exhaustive security audit.
## Integration
This package is an add-on module, not a standalone replacement for the parent repository's provider layer.
1. Copy `modules/guardrail_lab/` into the repository's `modules/` directory.
2. Copy `tests/test_guardrail_lab.py`, `tests/test_campaign.py`, and `tests/test_openai_compatible.py` into the repository's `tests/` directory.
3. Ensure the parent repository provides `modules.ai_scanner.providers.call_provider_messages(provider, messages, model=None)` for the native OpenAI, Anthropic, and Gemini routes. It should return `(actual_model, response_text, metadata)`.
4. Run the commands in [Quick start](#quick-start) from the repository root.
The OpenAI-compatible routes use the bundled `modules.guardrail_lab.openai_compatible` adapter. See [INTEGRATION.md](INTEGRATION.md) for the concise integration notes.
## Development and validation
Run the tests from the package/repository root:
```bash
python -m unittest discover -s tests -v
```
The v0.3.1 package was validated with its unit tests and CLI case listing. Unit tests use mocked provider responses; they do not establish that a live provider account, network endpoint, or specific model is reachable or behaves as expected. Run an authorized, low-budget live smoke test before relying on a provider integration.
## Version 0.3.1 hardening
- Enforces HTTPS for non-loopback compatible endpoints while retaining loopback HTTP for local inference.
- Rejects unsafe or malformed endpoint URL forms and validates response JSON structure.
- Validates positive finite request timeouts and handles malformed content-part entries defensively.
- Rejects duplicate and unknown case IDs.
- Enforces the `GL-009` then `GL-010` paired-turn prerequisite and skips the follow-up when setup fails.
- Excludes Python bytecode and cache directories from the release archive.
## Responsible use
Only assess systems for which you have explicit authorization. Follow provider terms, applicable law, rate limits, and your organization's disclosure process. Do not use this package to target third-party systems without permission, retrieve real secrets, or attempt harmful safeguard circumvention.
## License
See the repository's `LICENSE` file for the applicable license. If no license file is present, do not assume the code is licensed for redistribution or reuse.
