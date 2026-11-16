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

    def test_remote_http_is_rejected_even_without_key(self):
        with self.assertRaisesRegex(GuardrailRunError, "HTTPS is required"):
            call_openai_compatible([{"role": "user", "content": "x"}],
                                   model="m", base_url="http://api.example/v1")

    def test_remote_http_with_key_is_rejected_before_network_call(self):
        with patch.dict(os.environ, {"TEST_PROVIDER_KEY": "secret-token"}), \
             patch("urllib.request.urlopen") as urlopen:
            with self.assertRaisesRegex(GuardrailRunError, "HTTPS is required"):
                call_openai_compatible([{"role": "user", "content": "x"}],
                                       model="m", base_url="http://api.example/v1",
                                       api_key_env="TEST_PROVIDER_KEY")
            urlopen.assert_not_called()

    def test_non_object_json_response_is_rejected(self):
        with patch("urllib.request.urlopen", return_value=FakeResponse(["unexpected"])):
            with self.assertRaisesRegex(GuardrailRunError, "JSON object"):
                call_openai_compatible([{"role": "user", "content": "x"}],
                                       model="m", base_url="http://localhost/v1")

    def test_malformed_content_parts_are_handled_safely(self):
        response = {"choices": [{"message": {"content": [None, {"type": "text", "text": 7}, {"type": "text", "text": "safe"}]}}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(response)):
            _, text, _ = call_openai_compatible([{"role": "user", "content": "x"}],
                                                model="m", base_url="http://localhost/v1")
        self.assertEqual(text, "safe")

    def test_invalid_timeout_is_rejected(self):
        for value in (0, -1, True, float("inf"), float("nan"), 10**10000):
            with self.subTest(timeout=value):
                with self.assertRaisesRegex(GuardrailRunError, "timeout"):
                    call_openai_compatible(
                        [{"role": "user", "content": "x"}],
                        model="m",
                        base_url="http://localhost/v1",
                        timeout=value,
                    )

    def test_content_part_array_is_supported(self):
        response = {"choices": [{"message": {"content": [
            {"type": "text", "text": "one"}, {"type": "image", "text": "ignored"},
            {"type": "text", "text": "two"}
        ]}, "finish_reason": "stop"}]}
        with patch("urllib.request.urlopen", return_value=FakeResponse(response)):
            _, text, _ = call_openai_compatible([{"role": "user", "content": "x"}],
                                                model="m", base_url="http://localhost/v1")
        self.assertEqual(text, "one\ntwo")

    def test_transient_429_is_retried_then_succeeds(self):
        import io as _io
        import urllib.error as _urlerr
        response = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        attempts = {"n": 0}

        def flaky(request, timeout=90.0):
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise _urlerr.HTTPError(
                    request.full_url, 429, "slow down", {},
                    _io.BytesIO(b"slow down"))
            return FakeResponse(response)

        with patch("urllib.request.urlopen", side_effect=flaky), \
                patch("time.sleep"):
            _, text, _ = call_openai_compatible(
                [{"role": "user", "content": "x"}],
                model="m", base_url="http://localhost/v1")
        self.assertEqual(text, "ok")
        self.assertEqual(attempts["n"], 3)

    def test_5xx_retry_exhaustion_raises_guardrail_error(self):
        import io as _io
        import urllib.error as _urlerr

        def failing(request, timeout=90.0):
            raise _urlerr.HTTPError(
                request.full_url, 500, "err", {}, _io.BytesIO(b"boom"))

        with patch("urllib.request.urlopen", side_effect=failing) as urlopen, \
                patch("time.sleep"):
            with self.assertRaisesRegex(GuardrailRunError, "500"):
                call_openai_compatible([{"role": "user", "content": "x"}],
                                       model="m", base_url="http://localhost/v1")
        self.assertEqual(urlopen.call_count, 3)

    def test_connection_error_is_retried_then_succeeds(self):
        import urllib.error as _urlerr
        response = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        attempts = {"n": 0}

        def flaky(request, timeout=90.0):
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise _urlerr.URLError("connection reset")
            return FakeResponse(response)

        with patch("urllib.request.urlopen", side_effect=flaky), \
                patch("time.sleep"):
            _, text, _ = call_openai_compatible(
                [{"role": "user", "content": "x"}],
                model="m", base_url="http://localhost/v1")
        self.assertEqual(text, "ok")
        self.assertEqual(attempts["n"], 2)

    def test_incomplete_read_is_retried_then_succeeds(self):
        import http.client
        response = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
        attempts = {"n": 0}

        class FlakyResponse(FakeResponse):
            def read(self):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise http.client.IncompleteRead(b'{"choices"', 5)
                return super().read()

        def flaky(request, timeout=90.0):
            return FlakyResponse(response)

        with patch("urllib.request.urlopen", side_effect=flaky), \
                patch("time.sleep"):
            _, text, _ = call_openai_compatible(
                [{"role": "user", "content": "x"}],
                model="m", base_url="http://localhost/v1")
        self.assertEqual(text, "ok")
        self.assertEqual(attempts["n"], 2)

    def test_incomplete_read_exhaustion_raises_guardrail_error(self):
        import http.client

        class AlwaysIncomplete(FakeResponse):
            def read(self):
                raise http.client.IncompleteRead(b"", 1)

        with patch("urllib.request.urlopen",
                   return_value=AlwaysIncomplete({})) as urlopen, \
                patch("time.sleep"):
            with self.assertRaises(GuardrailRunError):
                call_openai_compatible([{"role": "user", "content": "x"}],
                                       model="m", base_url="http://localhost/v1")
        self.assertEqual(urlopen.call_count, 3)

    def test_hosted_presets_have_documented_base_urls(self):
        from modules.guardrail_lab.openai_compatible import PRESET_BASE_URLS

        expected = {
            "deepseek": "https://api.deepseek.com/v1",
            "glm": "https://open.bigmodel.cn/api/paas/v4",
            "moonshot": "https://api.moonshot.ai/v1",
            "nvidia": "https://integrate.api.nvidia.com/v1",
            "openrouter": "https://openrouter.ai/api/v1",
            "groq": "https://api.groq.com/openai/v1",
            "together": "https://api.together.xyz/v1",
        }
        for name, url in expected.items():
            with self.subTest(preset=name):
                self.assertEqual(PRESET_BASE_URLS[name], url)

    def test_preset_name_resolves_to_its_base_url(self):
        from modules.guardrail_lab.cli import _adapter

        with patch(
            "modules.guardrail_lab.cli.call_openai_compatible",
            return_value=("m", "ok", {}),
        ) as compat:
            call = _adapter("openrouter", "some-model")
            _, text, _ = call([{"role": "user", "content": "x"}])
        self.assertEqual(text, "ok")
        self.assertEqual(
            compat.call_args.kwargs["base_url"],
            "https://openrouter.ai/api/v1",
        )
        self.assertEqual(
            compat.call_args.kwargs["api_key_env"],
            "OPENROUTER_API_KEY",
        )

    def test_preset_key_env_override_wins(self):
        from modules.guardrail_lab.cli import _adapter

        with patch(
            "modules.guardrail_lab.cli.call_openai_compatible",
            return_value=("m", "ok", {}),
        ) as compat:
            call = _adapter(
                "deepseek", "deepseek-chat", api_key_env="MY_DEEPSEEK_KEY"
            )
            call([{"role": "user", "content": "x"}])
        self.assertEqual(
            compat.call_args.kwargs["api_key_env"],
            "MY_DEEPSEEK_KEY",
        )

    def test_cloudflare_1010_is_not_retried(self):
        import io
        import urllib.error
        def blocked(request, timeout=90.0):
            raise urllib.error.HTTPError(
                request.full_url,
                403,
                "Cloudflare block",
                {},
                io.BytesIO(b"error code: 1010"),
            )
        with patch(
            "urllib.request.urlopen",
            side_effect=blocked,
        ) as urlopen, patch("time.sleep") as sleep:
            with self.assertRaisesRegex(
                GuardrailRunError, "1010"
            ):
                call_openai_compatible(
                    [{"role": "user", "content": "test"}],
                    model="test-model",
                    base_url="http://localhost:11434/v1",
                )
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
