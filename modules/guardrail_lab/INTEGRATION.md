# Guardrail Lab integration notes

Guardrail Lab is integrated into this repository. It lives in `modules/guardrail_lab/`; its tests are `tests/test_guardrail_lab.py`, `tests/test_campaign.py`, and `tests/test_openai_compatible.py`.

## Provider layer

- Native OpenAI, Anthropic, and Gemini routes use the repository's shared adapter at `modules.ai_scanner.providers.call_provider_messages(provider, messages, model=None)`, which returns `(actual_model, response_text, metadata)`.
- OpenAI-compatible routes use the bundled `modules.guardrail_lab.openai_compatible` adapter.
- Run a single provider test against an authorized account and inspect the JSON evidence before running the full suite.

## Tests

Run the complete suite from the repository root:

```bash
python -m unittest discover -s tests -v
```

## Campaigns

The CLI also supports `--campaign`, `--budget`, `--variants`, `--delay`, `--max-seconds`, and `--no-adaptive`. See the module README for an example.

## Notes (v0.3.2)

- Campaign `--delay` and `--max-seconds` must be finite numbers.
- OpenAI-compatible remote endpoints must use HTTPS; HTTP is restricted to loopback local servers.
- GL-010 must be selected directly after GL-009.
