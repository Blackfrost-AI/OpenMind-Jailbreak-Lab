# Installation

## 1. Clone the repository

```bash
git clone https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab.git
cd OpenMind-Jailbreak-Lab
```

## 2. Requirements

- Python 3.10 or newer (CI runs Python 3.12).
- No third-party packages. Every module uses the Python standard library only.
- No build step and no virtual environment required (one is fine if you prefer it).

## 3. Verify the checkout

```bash
python -m unittest discover -s tests -v
python -m src.validate
python -m modules.guardrail_lab --list
python -m modules.jb002 list
```

The test suite (160 tests) should pass, the validator should report `VALIDATION PASSED` for the 56 benchmark cases, and the two list commands should print the Guardrail Lab cases and the JB-002 cases without making any API calls.

## 4. Provider credentials

Live tests need a provider API key. Set it as an environment variable — never put keys in source files, reports, command-line arguments, or commits.

| Provider | Variable |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic Claude | `ANTHROPIC_API_KEY` |
| Google Gemini | `GEMINI_API_KEY` or `GOOGLE_API_KEY` |

OpenAI-compatible endpoints (Guardrail Lab) use `OPENAI_COMPAT_API_KEY` by default, or another variable with `--api-key-env`. Local servers (Ollama, vLLM, LM Studio, llama.cpp, LocalAI) can omit the key.

## 5. First run

```bash
python -m modules.ai_scanner --provider gemini --output reports/gemini.json
python -m modules.guardrail_lab --provider gemini --output reports/gemini-guardrail.json
```

Check provider pricing and rate limits before running tests. Gemini's free tier allows 15 requests per minute on gemini-3.5-flash-lite — for campaigns, use `--delay 5` to stay under it.

## Module documentation

- [AI Scanner](modules/ai_scanner/README.md) — probes, providers, report format
- [Guardrail Lab](modules/guardrail_lab/README.md) — cases, campaigns, compatible endpoints
- [JB-002](modules/jb002/README.md) — manual test protocol, recording, validation
- [SCORING.md](SCORING.md) and [METHODOLOGY.md](METHODOLOGY.md) — benchmark scoring and method
