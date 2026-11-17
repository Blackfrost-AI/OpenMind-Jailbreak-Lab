# Vulnerability Registry and Research Export

The registry preserves findings for future campaigns and exports portable Markdown or JSON for manual review and disclosure. It does not submit reports to companies.

## Add a finding

Create a JSON file containing these required fields: finding_id, title, provider, model, category, status, discovered_at, evidence_ref, and summary. Optional fields include evidence_sha256, reproduction_steps, review_notes, repeat_runs, and repeat_successes.

Example:
```json
{
  "finding_id": "OM-FND-0001",
  "title": "Synthetic canary disclosure in untrusted source",
  "provider": "gemini",
  "model": "exact-model-id",
  "category": "indirect_prompt_injection",
  "status": "unverified",
  "discovered_at": "2026-11-16T12:00:00Z",
  "evidence_ref": "reports/run-001.json",
  "summary": "Describe observed behavior and limitations.",
  "reproduction_steps": "Record case ID, configuration and rerun command."
}
```

Add it with:
```bash
python -m modules.guardrail_lab.registry add --input finding.json\n# For a custom registry path, place --registry before the subcommand:\npython -m modules.guardrail_lab.registry --registry findings/research.jsonl list
```

Confirmed status requires an explicit --confirm-review flag, assessment=potential_guardrail_failure, reviewer notes, at least two repeat runs and at least two successful reproductions. The registry never promotes a model response automatically.

## Review and export

```bash
python -m modules.guardrail_lab.registry list
python -m modules.guardrail_lab.registry list --status intermittent
python -m modules.guardrail_lab.registry export --format markdown --out reports/findings.md
python -m modules.guardrail_lab.registry export --format json --out reports/findings.json
```

Each record receives a SHA-256 integrity checksum. This detects accidental edits but is not a digital signature or proof of provider origin. Keep original run reports alongside the registry and redact sensitive data before sharing exports.
