import tempfile
import unittest
from pathlib import Path

from modules.guardrail_lab.demo import build_demo_report, main


class SyntheticDemoTests(unittest.TestCase):
    def test_demo_is_explicitly_non_live_and_never_claims_confirmed_findings(self):
        report = build_demo_report()
        self.assertEqual(report["report_type"], "SYNTHETIC_DEMONSTRATION")
        self.assertTrue(report["provenance"]["synthetic"])
        self.assertFalse(report["provenance"]["live_model_test"])
        self.assertEqual(report["provenance"]["provider_calls"], 0)
        self.assertEqual(report["summary"]["confirmed_live_findings"], 0)
        self.assertTrue(all(row["provider"] == "SIMULATED_PROVIDER" for row in report["results"]))

    def test_cli_writes_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = str(Path(tmp) / "demo.json")
            self.assertEqual(main(["--output", output]), 0)
            self.assertTrue(Path(output).exists())
            self.assertIn("SYNTHETIC_DEMONSTRATION", Path(output).read_text())


if __name__ == "__main__":
    unittest.main()
