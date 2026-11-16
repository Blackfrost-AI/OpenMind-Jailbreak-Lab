# Repository integration checklist

1. Copy `modules/guardrail_lab/` into the repository's `modules/` directory.
2. Copy `tests/test_guardrail_lab.py`, `tests/test_campaign.py`, and `tests/test_openai_compatible.py` into `tests/`.
3. Confirm `modules/ai_scanner/providers.py` exposes `call_provider_messages(provider, messages, model=None)` and returns `(actual_model, response_text, metadata)`.
4. Run `python -m unittest discover -s tests -v`.
5. Run a single provider test against an authorized account and inspect the JSON evidence before running the full suite.
6. Add the test command to `.github/workflows/validate.yml` if desired.
7. Commit on a feature branch and review the diff before merging.

No repository files are changed by this archive; it is an integration package only.

For automated campaigns, the CLI also supports `--campaign`, `--budget`, `--variants`, `--delay`, `--max-seconds`, and `--no-adaptive`. See the package README for an example.


For v0.3.1, run the complete package suite with `python -m unittest discover -s tests -v`. OpenAI-compatible remote endpoints must use HTTPS; HTTP is restricted to loopback local servers. GL-010 must be selected directly after GL-009.
