"""Regression tests for Gemini provider metadata preservation."""
import os
import unittest
from unittest.mock import patch

from modules.ai_scanner import providers


class GeminiMetadataTests(unittest.TestCase):
    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False)
    @patch("modules.ai_scanner.providers._post")
    def test_prompt_block_feedback_is_preserved_without_candidates(
        self, post
    ):
        post.return_value = {
            "promptFeedback": {
                "blockReason": "SAFETY",
                "safetyRatings": [
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "probability": "HIGH",
                    }
                ],
            },
            "candidates": [],
        }

        model, text, metadata = providers.call_provider_messages(
            "gemini", [{"role": "user", "content": "benign control"}],
            model="gemini-test",
        )

        self.assertEqual(model, "gemini-test")
        self.assertEqual(text, "")
        self.assertEqual(
            metadata["prompt_feedback"]["blockReason"], "SAFETY"
        )
        self.assertEqual(
            metadata["prompt_feedback"]["safetyRatings"][0]["probability"],
            "HIGH",
        )
        self.assertEqual(metadata["finish_reason"], None)
        headers = post.call_args.args[1]
        self.assertEqual(headers["x-goog-api-key"], "test-key")
        self.assertNotIn("test-key", post.call_args.args[0])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False)
    @patch("modules.ai_scanner.providers._post")
    def test_candidate_safety_ratings_are_preserved(self, post):
        rating = {
            "category": "HARM_CATEGORY_HARASSMENT",
            "probability": "LOW",
            "blocked": False,
        }
        post.return_value = {
            "candidates": [{
                "finishReason": "STOP",
                "safetyRatings": [rating],
                "content": {"parts": [{"text": "Safe test response"}]},
            }]
        }

        _model, text, metadata = providers.call_provider_messages(
            "gemini", [{"role": "user", "content": "test"}],
            model="gemini-test",
        )

        self.assertEqual(text, "Safe test response")
        self.assertEqual(metadata["finish_reason"], "STOP")
        self.assertEqual(metadata["safety_ratings"], [rating])

    @patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False)
    @patch("modules.ai_scanner.providers._post")
    def test_missing_optional_feedback_keeps_legacy_metadata_shape(self, post):
        post.return_value = {
            "candidates": [{
                "finishReason": "STOP",
                "content": {"parts": [{"text": "OK"}]},
            }]
        }

        _model, text, metadata = providers.call_provider_messages(
            "gemini", [{"role": "user", "content": "test"}],
            model="gemini-test",
        )

        self.assertEqual(text, "OK")
        self.assertNotIn("prompt_feedback", metadata)
        self.assertEqual(metadata["safety_ratings"], [])


if __name__ == "__main__":
    unittest.main()
