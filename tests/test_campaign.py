import unittest
from modules.guardrail_lab.campaign import run_campaign

class CampaignTests(unittest.TestCase):
    def test_campaign_respects_budget(self):
        report = run_campaign(lambda messages: "The embedded instruction is untrusted.", provider="mock", budget=4)
        self.assertEqual(report["campaign"]["attempts"], 4)
        self.assertEqual(report["summary"]["total"], 4)

    def test_adaptive_expands_only_on_canary_signal(self):
        calls = []
        def safe_call(messages):
            calls.append(messages)
            return "The embedded instruction is untrusted and should not be followed."
        report = run_campaign(safe_call, provider="mock", budget=12, adaptive=True)
        self.assertEqual(report["campaign"]["attempts"], 12)
        self.assertTrue(all(r["variant"] == "baseline" for r in report["results"]))

    def test_adaptive_followups_are_bounded(self):
        n = {"count": 0}
        def canary_call(messages):
            n["count"] += 1
            return "CANARY-GL001" if "CANARY-GL001" in str(messages) else "untrusted"
        report = run_campaign(canary_call, provider="mock", budget=14, adaptive=True)
        gl1 = [r for r in report["results"] if r["case_id"] == "GL-001"]
        self.assertGreaterEqual(len(gl1), 2)
        self.assertLessEqual(len(gl1), 3)

    def test_campaign_can_select_cases_and_preserves_two_turn_context(self):
        captured = []
        def recorder(messages):
            captured.append(messages)
            return "The note is untrusted content."

        report = run_campaign(
            recorder, provider="mock", budget=2, adaptive=False,
            case_ids=["GL-009", "GL-010"],
        )
        self.assertEqual(report["campaign"]["attempts"], 2)
        self.assertEqual(report["campaign"]["case_ids"], ["GL-009", "GL-010"])
        self.assertEqual(captured[1][0]["role"], "user")
        self.assertEqual(captured[1][1]["role"], "assistant")
        self.assertEqual(captured[1][2]["role"], "user")

    def test_unknown_campaign_case_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown case ID"):
            run_campaign(lambda m: "ok", provider="mock", case_ids=["NOPE"])

    def test_duplicate_campaign_case_ids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate case IDs"):
            run_campaign(lambda m: "ok", provider="mock", case_ids=["GL-001", "GL-001"])

    def test_campaign_followup_requires_setup_case(self):
        with self.assertRaisesRegex(ValueError, "GL-009"):
            run_campaign(lambda m: "ok", provider="mock", case_ids=["GL-010"])

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            run_campaign(lambda m: "ok", provider="mock", budget=0)

    def test_non_integer_budget_and_variants_are_rejected(self):
        import math
        for bad in (math.nan, math.inf, 36.5, True, "36"):
            with self.assertRaisesRegex(
                    ValueError, "budget must be an integer"):
                run_campaign(lambda m: "ok", provider="mock", budget=bad)
        for bad in (math.nan, math.inf, 2.5, True, "2"):
            with self.assertRaisesRegex(
                    ValueError, "variants must be an integer"):
                run_campaign(lambda m: "ok", provider="mock", variants=bad)

    def test_non_finite_delay_is_rejected(self):
        import math
        with self.assertRaisesRegex(ValueError, "delay_seconds must be a finite"):
            run_campaign(lambda m: "ok", provider="mock", budget=2, delay_seconds=math.inf)
        with self.assertRaisesRegex(ValueError, "delay_seconds must be a finite"):
            run_campaign(lambda m: "ok", provider="mock", budget=2, delay_seconds=math.nan)

    def test_non_finite_max_seconds_is_rejected(self):
        import math
        with self.assertRaisesRegex(ValueError, "max_seconds must be a finite"):
            run_campaign(lambda m: "ok", provider="mock", budget=2, max_seconds=math.inf)
        with self.assertRaisesRegex(ValueError, "max_seconds must be a finite"):
            run_campaign(lambda m: "ok", provider="mock", budget=2, max_seconds=math.nan)

    def test_six_variants_expand_on_flag(self):
        from modules.guardrail_lab.campaign import VARIANTS
        self.assertEqual(len(VARIANTS), 6)
        def canary_call(messages):
            return "CANARY-GL001" if "CANARY-GL001" in str(messages) else "untrusted"
        report = run_campaign(
            canary_call, provider="mock", budget=12, adaptive=True,
            variants=6, case_ids=["GL-001"],
        )
        gl1 = [r for r in report["results"] if r["case_id"] == "GL-001"]
        self.assertEqual(len(gl1), 6)
        self.assertEqual(
            [r["variant"] for r in gl1],
            [name for name, _ in VARIANTS],
        )

    def test_variants_above_six_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "variants must be an integer"):
            run_campaign(lambda m: "ok", provider="mock", variants=7)

    def test_invalid_delay_values_are_rejected(self):
        import math
        for value in (True, "1", None, math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    run_campaign(
                        lambda _: "ok",
                        provider="mock",
                        budget=2,
                        delay_seconds=value,
                    )

    def test_invalid_max_seconds_values_are_rejected(self):
        import math
        for value in (True, "10", math.inf, math.nan, 0, -1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    run_campaign(
                        lambda _: "ok",
                        provider="mock",
                        budget=2,
                        max_seconds=value,
                    )

    def test_gl010_paired_context_uses_gl009_response(self):
        captured = []
        def recorder(messages):
            captured.append(messages)
            return "The note is untrusted content."
        report = run_campaign(
            recorder, provider="mock", budget=2, adaptive=True,
            variants=6, case_ids=["GL-009", "GL-010"],
        )
        self.assertEqual(report["campaign"]["attempts"], 2)
        # GL-010's paired conversation carries the GL-009 response as the
        # assistant turn, ahead of the GL-010 prompt.
        self.assertEqual(captured[1][0]["role"], "user")
        self.assertEqual(captured[1][1]["role"], "assistant")
        self.assertEqual(
            captured[1][1]["content"], "The note is untrusted content."
        )
        self.assertEqual(captured[1][2]["role"], "user")

if __name__ == "__main__":
    unittest.main()
