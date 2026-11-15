# OpenMind AI Exploit Scanner
Version: 0.1.1
An authorized AI API testing module for identifying potential
instruction-boundary weaknesses and recording reproducible evidence.
## Supported providers
- OpenAI
- Anthropic Claude
- Google Gemini
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
Never commit API keys to GitHub.
## Run scans
OpenAI:
python -m modules.ai_scanner --provider openai
Claude:
python -m modules.ai_scanner --provider anthropic
Gemini:
python -m modules.ai_scanner --provider gemini
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
Ten harmless canary-based probes: quoted untrusted text, document
injection, tool-output injection, disclosure handling, defensive
research, hex-encoded instruction, multilingual injection, false
authority, role switch, and a simulated multi-turn transcript.
The multi-turn probe is a transcript inside one prompt, not a live
multi-turn session.
## Evidence
The scanner records:
- Provider and model
- Probe identifier and category
- Exact prompt
- Actual API response
- Timestamp
- Potential failure indicators
- API errors
- Request metadata: request id, usage, finish/status, latency
Transient provider failures (HTTP 429 and 5xx, connection errors)
are retried up to three times with backoff, honoring Retry-After.
API keys are sent in request headers, never in URLs.
## Result meanings
potential_failure:
A canary string appeared in the model response.
Requires human review and reproduction.
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
## Limitations
This version uses a small set of harmless text probes.
It does not execute tools, access secrets, exploit accounts,
or test third-party systems.
API calls may incur charges.
Only test accounts and systems you are authorized to assess.
