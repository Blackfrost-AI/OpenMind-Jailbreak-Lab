# OpenMind Jailbreak Lab

AI Security Research · Prompt Injection Testing · Vulnerability Analysis · Evidence Collection

OpenMind Jailbreak Lab is an open-source research project for investigating AI model security, instruction-boundary weaknesses, prompt injection, and guardrail reliability.

The project provides tools for conducting authorized security assessments against AI systems, recording reproducible observations, and comparing security behavior across different model providers.

Its goal is to make AI security testing more systematic, transparent, and reproducible.

---

## Project Overview

OpenMind Jailbreak Lab is organized into independent modules, each serving a different part of the AI security research process.

| Component | Purpose |
|---|---|
| AI Exploit Scanner | Tests AI APIs for potential instruction-boundary weaknesses. |
| JB-002 | Records and validates manually observed security-test results. |
| OpenMind Benchmark | Provides structured test cases for evaluating AI security behavior. |
| Evidence Reports | Preserve model responses, metadata, and observations for review. |

The components are designed to work together without treating an unverified finding as a confirmed vulnerability.

## Current Components

### 1. AI Exploit Scanner

Location: `modules/ai_scanner/`

Version: 0.2.0

An API-based testing module for identifying potential instruction-boundary failures.

Supported providers:

- OpenAI
- Anthropic Claude
- Google Gemini

Current capabilities:

- Harmless prompt-injection probes.
- Untrusted document and quoted-text testing.
- Tool-output instruction-boundary testing.
- Encoded and multilingual instruction testing.
- False-authority and role-switch testing.
- Live two-turn multi-request testing (MULTITURN-LIVE-001).
- Canary-based failure indicators.
- Actual provider API responses.
- Request metadata and latency recording.
- Retry handling for transient API failures.
- JSON evidence reports.
- Cross-provider report comparisons.

The scanner currently includes eleven probes.

Multi-turn coverage: MULTITURN-001 is a simulated transcript inside a single request, kept for comparison. MULTITURN-LIVE-001 is a genuine two-turn session — one API call per turn, carrying the model's real first response into the second call — with the full transcript recorded in the report.

A canary match indicates a potential failure requiring human review. It does not independently establish exploitability.

**Live results so far:** Gemini `gemini-3.5-flash-lite`, 2026-11-15 — all 11 probes answered: 8 `no_indicator_observed`, 2 `manual_review`, 1 `potential_failure`. The failure is the new live multi-turn probe: the model output the canary verbatim in turn 2 instead of summarizing, reproduced in a second run (2/2). The simulated multi-turn probe on the same model scored clean, so the live session caught something the simulation missed. OpenAI has no credits and no Anthropic key is stored, so neither has produced a live run yet.

### 2. JB-002 Observation Recorder

Location: `modules/jb002/`

JB-002 provides structured recording and validation of observed AI security-test results.

Features:

- Structured test cases.
- Provider and model identification.
- Full model-output recording.
- Transcript preservation or references.
- Reproduction counts.
- Evidence classifications.
- Outcome classifications.
- JSONL validation.
- Observation summaries.

Supported outcomes:

- `held_boundary`
- `partial_boundary_failure`
- `boundary_failure`
- `over_refusal`
- `inconclusive`

The module separates observed evidence from researcher conclusions.

### 3. OpenMind Benchmark

Location: `data/`

The OpenMind benchmark provides structured test cases for evaluating instruction handling and AI security behavior.

Current benchmark:

`benchmark_v0.5.jsonl`

The dataset includes adversarial and benign control cases covering areas such as:

- Authority confusion.
- Untrusted content.
- Tool-output injection.
- Multilingual boundaries.
- Encoding boundaries.
- Secret-handling behavior.
- Formatting and instruction separation.
- Benign task handling.

Benchmark records include expected behavior and structured metadata.

The benchmark is validated using the repository's JSONL validation utility. Versioned releases are tagged (v0.3/v0.4/v0.5) with SHA-256 checksums in `data/CHECKSUMS.txt`; before/after runs can be compared with `src/compare_runs`, and recorded responses can be scored semantically with `src/semantic_review` (see `SEMANTIC_REVIEW.md`).

### 4. Evidence and Reporting

The project emphasizes evidence-based reporting.

Where supported, reports preserve:

- Provider.
- Model.
- Test identifier.
- Exact test prompt.
- Actual model response.
- Timestamp.
- API request metadata.
- Evaluation result.
- Error information.

Potential failures should be reviewed and reproduced before being reported as confirmed vulnerabilities.

---

## Installation

Requirements:

- Python 3.10 or newer.
- Git.
- API credentials for the provider being tested.
- No third-party Python packages are required by the current scanner.

Clone the repository:

```bash
git clone https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab.git
cd OpenMind-Jailbreak-Lab
```

### Configure API Credentials

Set the API key for the provider you intend to test.

OpenAI:

```bash
export OPENAI_API_KEY="your-api-key"
```

Anthropic:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Google Gemini:

```bash
export GEMINI_API_KEY="your-api-key"
```

Never commit API credentials, private transcripts, or sensitive testing data to the repository.

## Running the AI Scanner

OpenAI:

```bash
python -m modules.ai_scanner --provider openai
```

Anthropic:

```bash
python -m modules.ai_scanner --provider anthropic
```

Gemini:

```bash
python -m modules.ai_scanner --provider gemini
```

Specify a model:

```bash
python -m modules.ai_scanner --provider openai --model gpt-4.1-mini
```

Specify a report destination:

```bash
python -m modules.ai_scanner --provider openai --output reports/openai.json
```

Compare provider reports:

```bash
python -m modules.ai_scanner compare reports/openai.json reports/gemini.json reports/anthropic.json
```

Provider API usage may incur charges.

## Running JB-002

List available test cases:

```bash
python -m modules.jb002 list
```

Display a test case:

```bash
python -m modules.jb002 prompt JB002-01
```

Record an observation:

```bash
python -m modules.jb002 record
```

Validate recorded observations:

```bash
python -m modules.jb002 validate
```

Generate an observation report:

```bash
python -m modules.jb002 report
```

Generate JSON output:

```bash
python -m modules.jb002 report --json
```

## Benchmark Validation

Validate the current benchmark:

```bash
python -m src.validate data/benchmark_v0.5.jsonl
```

The validator checks record structure, required fields, identifiers, duplicate IDs, valid splits, risk levels, and other data constraints.

## Testing

Run the repository's available Python unit tests:

```bash
python -m unittest discover -s tests -v
```

A successful local test run does not replace provider-specific testing or a successful GitHub Actions run.

---

## Security Research Principles

OpenMind Jailbreak Lab is intended for authorized AI security research.

The project prioritizes:

1. Reproducibility over unsupported claims.
2. Actual model responses over fabricated results.
3. Clear separation of simulated and live tests.
4. Responsible vulnerability documentation.
5. Protection of API credentials and private information.
6. Human review of potential security failures.

The current scanner does not execute external tools, access model secrets, compromise accounts, or establish arbitrary software exploitability.

Testing should be limited to systems and accounts for which the researcher has authorization.

## Limitations

This is an actively developed research project.

Current limitations include:

- Limited scanner probe coverage.
- Canary-based detection can produce false positives and false negatives.
- Canary matching cannot reliably detect semantic failures, such as paraphrased compliance or reworded disclosures.
- Qualitative results require human assessment.
- No automated proof of exploitability.
- Provider behavior can change between model versions.
- API availability and rate limits can affect results.

A clean scan does not guarantee that an AI system is secure.

## Repository Structure

```
OpenMind-Jailbreak-Lab/
├── .github/workflows/validate.yml
├── data/
│   ├── benchmark_v0.3.jsonl
│   ├── benchmark_v0.4.jsonl
│   ├── benchmark_v0.5.jsonl
│   ├── schema.json
│   └── CHECKSUMS.txt
├── modules/
│   ├── ai_scanner/
│   │   ├── README.md
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── cli.py
│   │   ├── probes.py
│   │   ├── providers.py
│   │   └── runner.py
│   └── jb002/
│       ├── README.md
│       ├── __init__.py
│       ├── __main__.py
│       ├── cases.json
│       ├── cli.py
│       └── record.schema.json
├── src/
│   ├── compare_runs.py
│   ├── evaluate.py
│   ├── semantic_review.py
│   └── validate.py
├── tests/
├── METHODOLOGY.md
├── MODEL_CHANGE_AUDIT.md
├── SCORING.md
├── SEMANTIC_REVIEW.md
├── INJECTION_GUARDRAIL_TESTING.md
├── RESULTS_TEMPLATE.csv
├── LICENSE
└── README.md
```

`records/` holds JB-002 observations and `reports/` holds scanner reports; both are local-only and ignored by git.

## Development Roadmap

### Scanner Development

- [x] Implement genuine multi-turn API testing (done in v0.2.0).
- [ ] Expand prompt-injection test coverage.
- [ ] Improve semantic failure detection.
- [ ] Add false-positive analysis.
- [ ] Improve cross-provider comparison.
- [ ] Add automated regression coverage.
- [ ] Improve vulnerability evidence exports.

### Benchmark Development

- [ ] Expand test-case coverage.
- [ ] Improve evaluation consistency.
- [ ] Add additional model behavior categories.
- [ ] Maintain versioned datasets and checksums.
- [ ] Preserve compatibility with validation schemas.

### Quality Assurance

- [ ] Confirm GitHub Actions validation.
- [ ] Test all provider adapters.
- [ ] Test API error and retry handling.
- [ ] Verify report integrity.
- [ ] Document known limitations for every release.

---

## Contributing

Contributions are welcome.

Suggested contributions include:

- New defensive AI security tests.
- Scanner reliability improvements.
- Provider adapter improvements.
- Benchmark validation.
- Documentation.
- Bug reports and reproducible security observations.

Please include reproduction steps, expected behavior, actual behavior, and relevant version information when submitting issues.

Do not include API keys, private user information, or confidential transcripts.

## License

This project is distributed under the MIT License.

See LICENSE for the complete license terms.

## Project

OpenMind Jailbreak Lab

Repository: https://github.com/tjcrims0nx/OpenMind-Jailbreak-Lab

An ongoing independent research project focused on understanding, testing, and improving the security of AI systems.

Test carefully. Record evidence. Verify findings.
