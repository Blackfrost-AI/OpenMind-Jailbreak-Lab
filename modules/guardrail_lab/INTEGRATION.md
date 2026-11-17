# Guardrail Lab integration notes

Guardrail Lab lives in `modules/guardrail_lab/` and exposes 76 cases: 24 core tests plus 52 source-derived safe adaptations. Its implementation and source-corpus integration are covered by `tests/test_guardrail_lab.py`, `tests/test_campaign.py`, `tests/test_openai_compatible.py`, and the full repository test suite.

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

The CLI supports `--case` (repeatable), `--source-corpus`, `--campaign`, `--budget`, `--variants`, `--delay`, `--max-seconds`, and `--no-adaptive`. The default suite runs all 76 cases once; `--source-corpus` selects the 52 source-derived cases. Campaign mode is separately budget-limited and may not reach every selected case. Source-derived result records carry source ID, path, and SHA-256 provenance.

## Runtime and provenance guarantees

- Campaign `--delay` and `--max-seconds` must be finite numbers.
- OpenAI-compatible remote endpoints must use HTTPS; HTTP is restricted to loopback local servers.
- GL-010 must be selected directly after GL-009.


## One-switch research mode

Use `--research-mode` to run a bounded adversarial campaign with the six fixed,
reviewed framings and evidence-triggered follow-ups:

```bash
python -m modules.guardrail_lab --provider gemini --research-mode \
  --source-corpus --budget 100 \
  --output reports/source-research.json \
  --registry findings/registry.jsonl
```

The mode can be combined with repeatable `--case` selections or
`--source-corpus`. The configured budget caps scheduled requests; the campaign
time limit can also stop execution before every selected case is reached.
Registry records are unverified candidates, not confirmed findings. Human
transcript review and repeatability checks are required. `--no-adaptive` is
incompatible with `--research-mode`; use ordinary `--campaign` when adaptive
follow-ups should be disabled.

The evaluator records model output as data and does not execute tool calls or
instructions contained in responses. Run only against explicitly authorized
targets.
