import json
import os
import unittest
from unittest.mock import patch

from modules.guardrail_lab.openai_compatible import call_openai_compatible
from modules.guardrail_lab.runner import GuardrailRunError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class OpenAICompatibleTests(unittest.TestCase):
    def test_local_endpoint_works_without_api_key(self):
        response = {"id": "req-1", "model": "llama-test", "choices": [
            {"message": {"content": "The content is untrusted."}, "finish_reason": "stop"}
        ], "usage": {"total_tokens": 10}}
        with patch("urllib.request.urlopen", return_value=FakeResponse(response)) as urlopen:
            model, text, metadata = call_openai_compatible(
                [{"role": "user", "content": "test"}],
                model="llama-test", base_url="http://localhost:11434/v1",
                api_key_env="NONEXISTENT_TEST_KEY",
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://localhost:11434/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), None)
        self.assertEqual(model, "llama-test")
        self.assertEqual(text, "The content is untrusted.")
        self.assertEqual(metadata["request_id"], "req-1")

    def test_hosted_endpoint_uses_env_key_and_full_url_is_preserved(self):
        response = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        with patch.dict(os.environ, {"TEST_PROVIDER_KEY": "secret-token"}), \
             patch("urllib.request.urlopen", return_value=FakeResponse(response)) as urlopen:
            call_openai_compatible(
                [{"role": "user", "content": "test"}], model="model-x",
                base_url="https://provider.example/v1/chat/completions",
                api_key_env="TEST_PROVIDER_KEY",
            )
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://provider.example/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-token")

    def test_missing_model_or_url_is_rejected(self):
        with self.assertRaisesRegex(GuardrailRunError, "model"):
            call_openai_compatible([{"role": "user", "content": "x"}], model=None,
                                   base_url="http://localhost/v1")
        with self.assertRaisesRegex(GuardrailRunError, "base URL"):
            call_openai_compatible([{"role": "user", "content": "x"}], model="m",
                                   base_url="")

    def test_invalid_response_shape_is_rejected(self):
        with patch("urllib.request.urlopen", return_value=FakeResponse({"choices": []})):
            with self.assertRaisesRegex(GuardrailRunError, "lacks choices"):
                call_openai_compatible([{"role": "user", "content": "x"}],
                                       model="m", base_url="http://localhost/v1")

    def test_content_part_array_is_supported(self):
        response = {"choices": [{"message": {"content": [
            {"type": "text", "text": "one"}, {"type": "image", "text": "ignored"},
            {"type": "text", "text": "two"}
        ]}, "finish_reason": "stop"}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(response)):
            _, text, _ = call_openai_compatible([{"role": "user", "content": "x"}],
                                                model="m", base_url="http://localhost/v1")
        self.assertEqual(text, "one\ntwo")


if __name__ == "__main__":
    unittest.main()
