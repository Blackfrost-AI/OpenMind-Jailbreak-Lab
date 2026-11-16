"""Adapter for OpenAI-compatible local and hosted model endpoints.

Supports local inference servers (Ollama, vLLM, LM Studio, llama.cpp,
LocalAI, TGI when configured for its OpenAI-compatible route) and hosted
providers exposing /v1/chat/completions. No third-party dependency required.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Dict, List, Optional, Tuple

from .runner import GuardrailRunError

# Defaults are convenience presets only; --base-url overrides them.
PRESET_BASE_URLS = {
    "ollama": "http://localhost:11434/v1",
    "vllm": "http://localhost:8000/v1",
    "lm-studio": "http://localhost:1234/v1",
    "llama-cpp": "http://localhost:8080/v1",
    "localai": "http://localhost:8080/v1",
}


def _chat_url(base_url: str) -> str:
    value = base_url.strip().rstrip("/")
    if not value:
        raise GuardrailRunError("OpenAI-compatible base URL cannot be empty")
    if value.endswith("/chat/completions"):
        return value
    return value + "/chat/completions"


def call_openai_compatible(
    messages: List[Dict[str, str]],
    *,
    model: Optional[str],
    base_url: Optional[str] = None,
    api_key_env: str = "OPENAI_COMPAT_API_KEY",
    timeout: float = 90.0,
) -> Tuple[str, str, Dict]:
    """Call an OpenAI Chat Completions-compatible endpoint.

    Local endpoints may omit an API key. Hosted endpoints should set the
    environment variable named by api_key_env. The key is only sent in the
    Authorization header and is never written to evidence reports.
    """
    if not isinstance(messages, list) or not messages:
        raise GuardrailRunError("messages must be a non-empty list")
    for item in messages:
        if (not isinstance(item, dict)
                or item.get("role") not in ("system", "user", "assistant")
                or not isinstance(item.get("content"), str)):
            raise GuardrailRunError("messages must contain role/content text objects")

    chosen_model = model or os.getenv("OPENAI_COMPAT_MODEL")
    if not chosen_model:
        raise GuardrailRunError("Set --model or OPENAI_COMPAT_MODEL for this endpoint")
    chosen_url = base_url or os.getenv("OPENAI_COMPAT_BASE_URL")
    if not chosen_url:
        raise GuardrailRunError("Set a base URL with --base-url or OPENAI_COMPAT_BASE_URL")

    api_key = os.getenv(api_key_env) if api_key_env else None
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = json.dumps({"model": chosen_model, "messages": messages}).encode("utf-8")
    request = urllib.request.Request(_chat_url(chosen_url), data=payload,
                                     headers=headers, method="POST")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1500]
        raise GuardrailRunError(f"Compatible endpoint HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GuardrailRunError(f"Compatible endpoint connection failed: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GuardrailRunError(f"Compatible endpoint returned invalid JSON: {exc}") from exc

    try:
        choices = body["choices"]
        content = choices[0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GuardrailRunError("Compatible endpoint response lacks choices[0].message.content") from exc
    if isinstance(content, list):
        # Some compatible servers return content-part arrays.
        content = "\n".join(part.get("text", "") for part in content
                             if isinstance(part, dict) and part.get("type") == "text")
    if not isinstance(content, str):
        raise GuardrailRunError("Compatible endpoint returned non-text message content")

    actual_model = body.get("model") or chosen_model
    metadata = {
        "request_id": body.get("id"),
        "finish_reason": choices[0].get("finish_reason"),
        "usage": body.get("usage"),
        "endpoint_type": "openai-compatible",
        "latency_seconds": round(time.monotonic() - started, 3),
    }
    return actual_model, content, {key: value for key, value in metadata.items() if value is not None}
