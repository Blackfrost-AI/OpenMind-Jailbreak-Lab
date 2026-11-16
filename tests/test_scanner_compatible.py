import os
import unittest
from unittest import mock

from modules.ai_scanner.providers import ProviderError, call_provider_messages

MESSAGES = [{"role": "user", "content": "hello"}]
BODY = {
    "id": "chatcmpl-1",
    "model": "test-model",
    "choices": [
        {"message": {"content": "hi"}, "finish_reason": "stop"}
    ],
    "usage": {"prompt_tokens": 1},
}


class CompatibleProviderTests(unittest.TestCase):
    def _call(self, fake_body, env, **kwargs):
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "modules.ai_scanner.providers._post",
            return_value=fake_body,
        ) as post:
            result = call_provider_messages(
                "openai-compatible", MESSAGES, **kwargs
            )
            return result, post

    def test_posts_to_chat_completions_with_bearer_auth(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "https://example.com/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
            "OPENAI_COMPAT_API_KEY": "test-key",
        }
        (model, text, metadata), post = self._call(BODY, env)
        self.assertEqual(model, "test-model")
        self.assertEqual(text, "hi")
        self.assertEqual(metadata["endpoint_type"], "openai-compatible")
        url, headers, payload = post.call_args.args
        self.assertEqual(url, "https://example.com/v1/chat/completions")
        self.assertEqual(headers["Authorization"], "Bearer test-key")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(payload["messages"], MESSAGES)

    def test_content_part_array_is_joined(self):
        body = {
            "choices": [
                {"message": {"content": [
                    {"type": "text", "text": "one"},
                    {"type": "text", "text": "two"},
                ]}}
            ]
        }
        env = {
            "OPENAI_COMPAT_BASE_URL": "http://localhost:11434/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
        }
        (_, text, _), _ = self._call(body, env)
        self.assertEqual(text, "one\ntwo")

    def test_missing_base_url_is_rejected(self):
        env = {"OPENAI_COMPAT_MODEL": "test-model"}
        with self.assertRaisesRegex(ProviderError, "base URL"):
            self._call(BODY, env)

    def test_missing_model_is_rejected(self):
        env = {"OPENAI_COMPAT_BASE_URL": "http://localhost:11434/v1"}
        with self.assertRaisesRegex(ProviderError, "model"):
            self._call(BODY, env)

    def test_invalid_response_shape_is_rejected(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "http://localhost:11434/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
        }
        for body in (
            {"choices": []},
            {"choices": "nope"},
            {"choices": [{"message": {}}]},
            {"choices": [{"message": {"content": 123}}]},
            {},
        ):
            with self.subTest(body=body):
                with self.assertRaises(ProviderError):
                    self._call(body, env)

    def test_local_endpoint_works_without_api_key(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "http://localhost:11434/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
        }
        (_, _, _), post = self._call(BODY, env)
        self.assertNotIn("Authorization", post.call_args.args[1])

    def test_remote_http_is_rejected_before_network_call(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "http://example.com/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
        }
        with mock.patch.dict(os.environ, env, clear=True), mock.patch(
            "modules.ai_scanner.providers._post"
        ) as post:
            with self.assertRaisesRegex(ProviderError, "HTTPS"):
                call_provider_messages("openai-compatible", MESSAGES)
            post.assert_not_called()

    def test_url_with_credentials_is_rejected(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "https://user:pass@example.com/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
        }
        with self.assertRaisesRegex(ProviderError, "credentials"):
            self._call(BODY, env)

    def test_full_chat_completions_path_is_preserved(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "https://example.com/v1/chat/completions",
            "OPENAI_COMPAT_MODEL": "test-model",
            "OPENAI_COMPAT_API_KEY": "k",
        }
        (_, _, _), post = self._call(BODY, env)
        self.assertEqual(
            post.call_args.args[0],
            "https://example.com/v1/chat/completions",
        )

    def test_explicit_base_url_beats_env(self):
        env = {
            "OPENAI_COMPAT_BASE_URL": "https://env.example.com/v1",
            "OPENAI_COMPAT_MODEL": "test-model",
        }
        (_, _, _), post = self._call(
            BODY, env, base_url="https://explicit.example.com/v1"
        )
        self.assertEqual(
            post.call_args.args[0],
            "https://explicit.example.com/v1/chat/completions",
        )


class CompatibleCliTests(unittest.TestCase):
    def test_cli_accepts_compatible_provider_options(self):
        from modules.ai_scanner.cli import main

        with mock.patch(
            "modules.ai_scanner.cli.run",
            return_value=({"results": []}, "/tmp/out.json"),
        ) as run:
            code = main([
                "--provider", "openai-compatible",
                "--model", "test-model",
                "--base-url", "http://localhost:11434/v1",
                "--api-key-env", "MY_KEY",
                "--output", "/tmp/out.json",
            ])
        self.assertEqual(code, 0)
        run.assert_called_once_with(
            "openai-compatible", "test-model", "/tmp/out.json",
            base_url="http://localhost:11434/v1",
            api_key_env="MY_KEY",
        )

    def test_cli_requires_base_url_for_compatible_provider(self):
        from modules.ai_scanner.cli import main

        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(SystemExit):
                main(["--provider", "openai-compatible", "--model", "m"])


if __name__ == "__main__":
    unittest.main()
