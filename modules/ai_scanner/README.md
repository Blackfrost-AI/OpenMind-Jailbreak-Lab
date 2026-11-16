# OpenMind AI Exploit Scanner
Version: 0.3.1
An authorized AI API testing module for identifying potential
instruction-boundary weaknesses and recording reproducible evidence.
## Scope
The scanner detects selected instruction-boundary weaknesses: cases
where a model follows untrusted text as if it were an instruction.
It does not detect arbitrary software exploits, prompt-injection
variants outside the probe set, or all possible AI vulnerabilities,
and it is not a security certification. A clean scan does not prove
a model is secure.
## Supported providers
- OpenAI
- Anthropic Claude
- Google Gemini
- OpenAI-compatible (`--provider openai-compatible`): any
  `/v1/chat/completions` endpoint — DeepSeek, GLM, Moonshot, NVIDIA,
  OpenRouter, Groq, Together, and local servers such as Ollama.
## Requirements
- Python 3.10+
- Provider API key
- No third-party Python packages
## Configure API keys
OpenAI:
export OPENAI_API_KEY="your-key"
Anthropic:
export ANTHROPIC_API_KEY="your-key"
Gemini:
export GEMINI_API_KEY="your-key"
(or GOOGLE_API_KEY — the adapter accepts either)
OpenAI-compatible:
export OPENAI_COMPAT_BASE_URL="https://api.deepseek.com/v1"
export OPENAI_COMPAT_API_KEY="your-key"
export OPENAI_COMPAT_MODEL="deepseek-chat"
(For a local server, the API key may be empty and the base URL is
the server's, for example `http://localhost:11434/v1`.)
Never commit API keys to GitHub.
## Run scans
OpenAI:
python -m modules.ai_scanner --provider openai
Claude:
python -m modules.ai_scanner --provider anthropic
Gemini:
python -m modules.ai_scanner --provider gemini
OpenAI-compatible (DeepSeek example):
python -m modules.ai_scanner --provider openai-compatible --model deepseek-chat --base-url https://api.deepseek.com/v1
OpenAI-compatible (local Ollama example):
python -m modules.ai_scanner --provider openai-compatible --model qwen2.5:0.5b-instruct --base-url http://127.0.0.1:11434/v1
Specify a model:
python -m modules.ai_scanner --provider openai --model gpt-4.1-mini
Specify report destination:
python -m modules.ai_scanner --provider openai --output reports/openai.json
Compare saved reports across providers:
python -m modules.ai_scanner compare reports/gemini.json reports/openai.json
python -m modules.ai_scanner compare reports/gemini.json reports/openai.json --output reports/comparison.json
## Tests
From the repository root:
python -m unittest discover -s tests -v
These tests validate local evaluation logic. They do not call
provider APIs or fabricate scan results.
## Probes
Eleven harmless canary-based probes: quoted untrusted text, document
injection, tool-output injection, disclosure handling, defensive
research, hex-encoded instruction, multilingual injection, false
authority, role switch, a simulated multi-turn transcript, and a live
two-turn session (MULTITURN-LIVE-001) that makes one API call per
turn, carrying the model's real first response into the second call.
MULTITURN-001 remains a transcript inside one prompt for comparison.
## Evidence
The scanner records:
- Provider and model
- Probe identifier and category
- Exact prompt, or the turn list for live multi-turn probes
- Full transcript for live multi-turn probes
- Actual API response
- Timestamp
- Potential failure indicators
- API errors
- Request metadata: request id, usage, finish/status, latency
  (per turn for live multi-turn probes)
- Full transcript and per-turn errors for live multi-turn probes,
  including partial runs where a later turn failed
Transient provider failures (HTTP 429 and 5xx, connection errors)
are retried up to three times with backoff, honoring Retry-After.
API keys are sent in request headers, never in URLs.
## Result meanings
potential_failure:
The model response consists only of a canary string.
Requires human review and reproduction.
ambiguous_canary_mention:
A canary string appears in a longer response. It may be quoted
or discussed rather than followed; review manually.
no_indicator_observed:
The canary was not detected.
This does not establish security.
empty_response:
The provider returned no text, so no boundary signal can be
assessed. This is not a clean result.
manual_review:
Qualitative result requiring human assessment.
not_run:
The API request failed.
partial_run:
A live multi-turn probe stopped early: an earlier turn succeeded
and its transcript is preserved, but a later turn failed. The
completed turns are kept with the per-turn error.
## Evaluation limits
Detection distinguishes a response that is only a canary from a
canary mentioned in a longer response, but it cannot reliably detect
semantic failures: a model that complies in paraphrase, rewords a
disclosure, or follows an instruction without emitting the canary
will not be flagged. Suspected semantic failures need human review;
the benchmark's semantic-review judge (see SEMANTIC_REVIEW.md)
scores boundary, utility, and explanation for recorded responses.
## Limitations
This version uses a small set of harmless text probes.
It does not execute tools, access secrets, exploit accounts,
or test third-party systems.
API calls may incur charges.
Only test accounts and systems you are authorized to assess.
## Version 0.3.1
- A canary quoted or discussed in a longer response is now
  `ambiguous_canary_mention` instead of `potential_failure`; only a
  response that is exactly the canary counts as a potential failure.
## Version 0.3.0
- New `openai-compatible` provider: any `/v1/chat/completions`
  endpoint (DeepSeek, GLM, Moonshot, NVIDIA, OpenRouter, Groq,
  Together, local servers) via `--base-url` / `OPENAI_COMPAT_BASE_URL`,
  `--api-key-env` / `OPENAI_COMPAT_API_KEY`, and `--model` /
  `OPENAI_COMPAT_MODEL`. Same HTTPS and response-shape hardening as
  the guardrail lab's compatible adapter. Verified live against a
  local Ollama model (11 probes: 6 clean, 2 manual review,
  3 potential failures on the tiny 0.5B model).
