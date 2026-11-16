import unittest
from modules.guardrail_lab.openai_compatible import (
    PRESET_BASE_URLS,
    PRESET_API_KEY_ENVS,
)

HOSTED = (
    "deepseek",
    "glm",
    "moonshot",
    "nvidia",
    "openrouter",
    "groq",
    "together",
)
LOCAL = (
    "ollama",
    "vllm",
    "lm-studio",
    "llama-cpp",
    "localai",
)


class ProviderPresetTests(unittest.TestCase):
    def test_hosted_provider_presets_exist(self):
        self.assertTrue(set(HOSTED).issubset(PRESET_BASE_URLS))

    def test_hosted_provider_urls_use_https(self):
        for provider in HOSTED:
            with self.subTest(provider=provider):
                self.assertTrue(
                    PRESET_BASE_URLS[provider].startswith("https://")
                )

    def test_hosted_provider_key_environment_variables(self):
        expected = {
            "deepseek": "DEEPSEEK_API_KEY",
            "glm": "ZHIPUAI_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
            "nvidia": "NVIDIA_API_KEY",
            "openrouter": "OPENROUTER_API_KEY",
            "groq": "GROQ_API_KEY",
            "together": "TOGETHER_API_KEY",
        }
        for provider, env_name in expected.items():
            with self.subTest(provider=provider):
                self.assertEqual(
                    PRESET_API_KEY_ENVS[provider],
                    env_name,
                )

    def test_local_presets_remain_available(self):
        self.assertTrue(set(LOCAL).issubset(PRESET_BASE_URLS))

    def test_local_presets_have_no_provider_key_env(self):
        for provider in LOCAL:
            with self.subTest(provider=provider):
                self.assertNotIn(provider, PRESET_API_KEY_ENVS)


if __name__ == "__main__":
    unittest.main()
