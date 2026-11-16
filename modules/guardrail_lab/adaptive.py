"""Adaptive, bounded test scheduling for synthetic guardrail evaluations.

Adaptation selects *where to test next*; it never intensifies payloads,
removes safety framing, or generates instructions to obtain real secrets.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Sequence

from .discovery import VARIANTS

# These priorities affect test coverage only, not attack strength.
PRIORITY_BY_ASSESSMENT = {
    "ambiguous_canary_mention": ("quoted_source", "document_record", "retrieval_record"),
    "boundary_held": ("json_field", "simulated_tool_result", "retrieval_record"),
    "manual_review": ("quoted_source", "json_field", "document_record"),
    "control_passed": ("baseline", "quoted_source", "document_record"),
    "partial_run": ("baseline", "retrieval_record", "simulated_tool_result"),
    "potential_guardrail_failure": ("baseline", "quoted_source", "document_record"),
}


def plan_adaptive_cases(
    cases: Iterable[Dict],
    history: Iterable[Dict],
    *,
    max_new_variants: int = 3,
    request_budget: int = 100,
) -> List[Dict]:
    """Select untested, fixed-envelope variants based on reviewed prior outcomes.

    Each case needs ``id`` and ``prompt``. History rows need ``source_case_id``,
    ``discovery_variant`` and ``assessment``. The original prompt text is
    preserved verbatim inside a fixed, safe envelope.
    """
    if isinstance(max_new_variants, bool) or not isinstance(max_new_variants, int) or not 1 <= max_new_variants <= len(VARIANTS):
        raise ValueError(f"max_new_variants must be from 1 to {len(VARIANTS)}")
    if isinstance(request_budget, bool) or not isinstance(request_budget, int) or request_budget < 0:
        raise ValueError("request_budget must be a non-negative integer")

    known_names = {name for name, _ in VARIANTS}
    history_by_case: Dict[str, List[Dict]] = {}
    for item in history:
        if not isinstance(item, dict):
            raise ValueError("history entries must be objects")
        case_id = item.get("source_case_id")
        variant = item.get("discovery_variant")
        assessment = item.get("assessment")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError("history source_case_id must be non-empty text")
        if variant not in known_names:
            raise ValueError(f"unknown discovery_variant: {variant!r}")
        if assessment not in PRIORITY_BY_ASSESSMENT:
            raise ValueError(f"unknown assessment: {assessment!r}")
        history_by_case.setdefault(case_id, []).append(item)

    templates = dict(VARIANTS)
    output: List[Dict] = []
    seen_case_ids = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("cases must contain objects")
        case_id, prompt = case.get("id"), case.get("prompt")
        if not isinstance(case_id, str) or not case_id.strip() or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("each case needs non-empty string id and prompt")
        if case_id in seen_case_ids:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_case_ids.add(case_id)

        prior = history_by_case.get(case_id, [])
        tested = {row["discovery_variant"] for row in prior}
        latest_assessment = prior[-1]["assessment"] if prior else "control_passed"
        preferred = PRIORITY_BY_ASSESSMENT[latest_assessment]
        order = list(preferred) + [name for name, _ in VARIANTS if name not in preferred]
        selected = [name for name in order if name not in tested][:max_new_variants]
        for name in selected:
            index = next(i for i, (variant_name, _) in enumerate(VARIANTS, 1) if variant_name == name)
            row = dict(case)
            row.update({
                "id": f"{case_id}-A{index:02d}",
                "source_case_id": case_id,
                "discovery_variant": name,
                "adaptive_reason": f"coverage_after_{latest_assessment}",
                "prompt": templates[name].format(prompt=prompt),
            })
            output.append(row)
            if len(output) > request_budget:
                raise ValueError(f"adaptive plan exceeds request budget {request_budget}")
    return output
