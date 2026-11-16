"""Provider-neutral adapter contract tests; all HTTP is mocked."""
import os
import unittest
from unittest.mock import patch

from modules.ai_scanner import providers


MESSAGES = [
    {"role": "user", "content": "Summarize this harmless sample."},
    {"role": "assistant", "content": "The sample is a short note."},
    {"role": "user", "content": "Now identify its main point."},
]


class ProviderMatrixContractTests(unittest.TestCase):
    def _call(self, provider, env, response, **kwargs):
        with patch.dict(os.environ, env, clear=True), patch(
            "modules.ai_scanner.providers._post", return_value=response
        ) as post:
            result = providers.call_provider_messages(
                provider, MESSAGES, model="matrix-test-model", **kwargs
            )
        return result, post

    def test_openai_responses_api_contract(self):
        (model, text, metadata), post = self._call(
            "openai",
            {"OPENAI_API_KEY": "unit-test-key"},
            {
                "id": "resp-test",
                "status": "completed",
                "model": "matrix-test-model",
                "output": [{"content": [{"type": "output_text", "text": "Main point."}]}],
                "usage": {"input_tokens": 12, "output_tokens": 3},
            },
        )
        self.assertEqual((model, text), ("matrix-test-model", "Main point."))
        self.assertEqual(metadata["request_id"], "resp-test")
        self.assertEqual(post.call_args.args[0], "https://api.openai.com/v1/responses")
        self.assertEqual(post.call_args.args[2]["input"], MESSAGES)
        self.assertEqual(post.call_args.args[1]["Authorization"], "Bearer unit-test-key")

    def test_anthropic_messages_api_contract(self):
        (model, text, metadata), post = self._call(
            "anthropic",
            {"ANTHROPIC_API_KEY": "unit-test-key"},
            {
                "id": "msg-test",
                "model": "matrix-test-model",
                "stop_reason": "end_turn",
                "content": [{"type": "text", "text": "Main point."}],
                "usage": {"input_tokens": 12, "output_tokens": 3},
            },
        )
        self.assertEqual((model, text), ("matrix-test-model", "Main point."))
        self.assertEqual(metadata["request_id"], "msg-test")
        self.assertEqual(post.call_args.args[0], "https://api.anthropic.com/v1/messages")
        self.assertEqual(post.call_args.args[2]["messages"], MESSAGES)
        self.assertEqual(post.call_args.args[1]["x-api-key"], "unit-test-key")

    def test_gemini_generate_content_contract_and_multiturn_mapping(self):
        (model, text, metadata), post = self._call(
            "gemini",
            {"GEMINI_API_KEY": "unit-test-key"},
            {
                "responseId": "gem-test",
                "modelVersion": "matrix-test-model",
                "candidates": [{
                    "finishReason": "STOP",
                    "content": {"parts": [{"text": "Main point."}]},
                }],
            },
        )
        self.assertEqual((model, text), ("matrix-test-model", "Main point."))
        self.assertEqual(metadata["request_id"], "gem-test")
        self.assertEqual(post.call_args.args[2]["contents"], [
            {"role": "user", "parts": [{"text": "Summarize this harmless sample."}]},
            {"role": "model", "parts": [{"text": "The sample is a short note."}]},
            {"role": "user", "parts": [{"text": "Now identify its main point."}]},
        ])
        self.assertEqual(post.call_args.args[1]["x-goog-api-key"], "unit-test-key")
        self.assertNotIn("unit-test-key", post.call_args.args[0])

    def test_openai_compatible_contract_covers_hosted_and_local_endpoints(self):
        (model, text, metadata), post = self._call(
            "openai-compatible",
            {"MATRIX_KEY": "unit-test-key"},
            {
                "id": "compat-test",
                "model": "matrix-test-model",
                "choices": [{
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "Main point."},
                }],
            },
            base_url="https://provider.example/v1",
            api_key_env="MATRIX_KEY",
        )
        self.assertEqual((model, text), ("matrix-test-model", "Main point."))
        self.assertEqual(metadata["endpoint_type"], "openai-compatible")
        self.assertEqual(post.call_args.args[0], "https://provider.example/v1/chat/completions")
        self.assertEqual(post.call_args.args[2]["messages"], MESSAGES)
        self.assertEqual(post.call_args.args[1]["Authorization"], "Bearer unit-test-key")

    def test_openai_compatible_localhost_allows_no_api_key(self):
        (model, text, _metadata), post = self._call(
            "openai-compatible",
            {},
            {
                "choices": [{
                    "message": {"role": "assistant", "content": "Local response."},
                }],
            },
            base_url="http://127.0.0.1:11434/v1",
        )
        self.assertEqual((model, text), ("matrix-test-model", "Local response."))
        self.assertNotIn("Authorization", post.call_args.args[1])


if __name__ == "__main__":
    unittest.main()
