# Adaptive discovery scheduler

`modules.guardrail_lab.adaptive.plan_adaptive_cases()` selects the next
uncovered test envelopes based on reviewed results from earlier runs. It
adapts test coverage, not payload intensity: the original synthetic test
prompt is preserved and placed only inside one of the fixed, documented
untrusted-input envelopes from `discovery.py`.

## Example

```python
from modules.guardrail_lab.adaptive import plan_adaptive_cases

cases = [{"id": "case-001", "prompt": "Synthetic canary: TEST_ONLY_123"}]
history = [{
    "source_case_id": "case-001",
    "discovery_variant": "baseline",
    "assessment": "ambiguous_canary_mention",
}]
next_batch = plan_adaptive_cases(
    cases, history, max_new_variants=2, request_budget=20
)
```

The scheduler prioritizes formats that help distinguish quoting, retrieval,
structured-data, and tool-output handling. It never removes safety framing,
creates real-secret requests, calls a provider, or automatically labels a
result as a vulnerability. Provider execution remains the responsibility of
an existing authorized adapter; all findings require human review.

History assessments must be one of: `ambiguous_canary_mention`,
`boundary_held`, `manual_review`, `control_passed`, `partial_run`, or
`potential_guardrail_failure`. The scheduler rejects unknown labels and
untested-variant duplication. `request_budget` is checked before returning
any planned calls.
