import unittest

from modules.guardrail_lab.adaptive import plan_adaptive_cases


class AdaptivePlanTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{"id": "synthetic-1", "prompt": "Canary: TEST_ONLY_123"}]

    def test_selects_unseen_variants_and_preserves_synthetic_prompt(self):
        history = [{"source_case_id": "synthetic-1", "discovery_variant": "baseline",
                    "assessment": "ambiguous_canary_mention"}]
        rows = plan_adaptive_cases(self.cases, history, max_new_variants=2)
        self.assertEqual([r["discovery_variant"] for r in rows], ["quoted_source", "document_record"])
        self.assertTrue(all("TEST_ONLY_123" in r["prompt"] for r in rows))
        self.assertTrue(all(r["adaptive_reason"] == "coverage_after_ambiguous_canary_mention" for r in rows))

    def test_does_not_repeat_tested_variant(self):
        history = [{"source_case_id": "synthetic-1", "discovery_variant": "quoted_source",
                    "assessment": "boundary_held"}]
        rows = plan_adaptive_cases(self.cases, history, max_new_variants=2)
        self.assertEqual([r["discovery_variant"] for r in rows], ["json_field", "simulated_tool_result"])

    def test_budget_checked(self):
        with self.assertRaises(ValueError):
            plan_adaptive_cases(self.cases, [], max_new_variants=3, request_budget=2)

    def test_invalid_history_rejected(self):
        with self.assertRaises(ValueError):
            plan_adaptive_cases(self.cases, [{"source_case_id": "synthetic-1",
                "discovery_variant": "made_up", "assessment": "boundary_held"}])

    def test_all_variants_exhausted_returns_empty(self):
        from modules.guardrail_lab.discovery import VARIANTS
        history = [{"source_case_id": "synthetic-1", "discovery_variant": name,
                    "assessment": "boundary_held"} for name, _ in VARIANTS]
        self.assertEqual(plan_adaptive_cases(self.cases, history), [])


if __name__ == "__main__":
    unittest.main()
