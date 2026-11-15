"""Minimal standard-library adapters for provider APIs."""
import json
import os
import urllib.error
import urllib.request
from urllib.parse import quote


class ProviderError(RuntimeError):
    """Raised when a provider request fails."""


def _post(url, headers, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise ProviderError(f"HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ProviderError(str(exc)) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError(f"Invalid provider response: {exc}") from exc


def call_provider(provider, prompt, model=None):
    provider = provider.lower()
    # OPENAI
    if provider == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ProviderError("OPENAI_API_KEY is not set")
        model = model or os.getenv(
            "OPENAI_MODEL",
            "gpt-4.1-mini",
        )
        body = _post(
            "https://api.openai.com/v1/responses",
            {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            {
                "model": model,
                "input": prompt,
            },
        )
        text = "\n".join(
            item.get("text", "")
            for output_item in body.get("output", [])
            for item in output_item.get("content", [])
            if item.get("type") == "output_text"
        )
        return model, text
    # ANTHROPIC
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        model = model or os.getenv(
            "ANTHROPIC_MODEL",
            "claude-3-7-sonnet-latest",
        )
        body = _post(
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            {
                "model": model,
                "max_tokens": 1200,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            },
        )
        text = "\n".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        return model, text
    # GOOGLE GEMINI
    if provider == "gemini":
        key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )
        if not key:
            raise ProviderError(
                "GEMINI_API_KEY or GOOGLE_API_KEY is not set"
            )
        model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash",
        )
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{quote(model, safe='')}:generateContent"
            f"?key={quote(key)}"
        )
        body = _post(
            url,
            {"Content-Type": "application/json"},
            {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
        )
        text = "\n".join(
            part.get("text", "")
            for candidate in body.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
        )
        return model, text
    raise ProviderError(f"Unsupported provider: {provider}")
