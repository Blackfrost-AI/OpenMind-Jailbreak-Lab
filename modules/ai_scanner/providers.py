"""Minimal standard-library adapters for provider APIs."""
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import quote


class ProviderError(RuntimeError):
    """Raised when a provider request fails."""


MAX_ATTEMPTS = 3
BACKOFF_BASE_SECONDS = 2.0
BACKOFF_MAX_SECONDS = 60.0


def _present(fields):
    """Drop keys whose value is None, so metadata only carries what the
    provider actually returned."""
    return {key: value for key, value in fields.items() if value is not None}


def _sleep_before_retry(attempt, headers):
    """Backoff before a retry: honor Retry-After when the provider sent
    one, otherwise exponential backoff, capped."""
    delay = None
    if headers is not None:
        raw = headers.get("Retry-After")
        if raw:
            try:
                delay = float(raw)
            except ValueError:
                delay = None
    if delay is None:
        delay = BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
    time.sleep(min(delay, BACKOFF_MAX_SECONDS))


def _post(url, headers, payload, timeout=60, max_attempts=MAX_ATTEMPTS):
    """POST JSON and return the parsed body.

    Retries transient failures (HTTP 429, HTTP 5xx, connection errors,
    timeouts) up to max_attempts times. Other 4xx errors fail at once:
    retrying a bad request cannot succeed.
    """
    data = json.dumps(payload).encode("utf-8")
    attempt = 0
    while True:
        attempt += 1
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
            retryable = exc.code == 429 or exc.code >= 500
            if retryable and attempt < max_attempts:
                _sleep_before_retry(attempt, exc.headers)
                continue
            raise ProviderError(f"HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < max_attempts:
                _sleep_before_retry(attempt, None)
                continue
            raise ProviderError(str(exc)) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError(f"Invalid provider response: {exc}") from exc


def _with_latency(metadata, started):
    metadata["latency_seconds"] = round(time.monotonic() - started, 3)
    return metadata


def _gemini_content(message):
    """Map one chat message to a Gemini content block."""
    role = "model" if message["role"] == "assistant" else "user"
    return {"role": role, "parts": [{"text": message["content"]}]}


def call_provider_messages(provider, messages, model=None):
    """Call one provider with a full message list and return
    (model, text, metadata).

    messages is a list of {"role": "user"|"assistant", "content": str}
    in conversation order, so multi-turn sessions send the real
    conversation so far. Single-turn callers pass one user message.
    metadata carries the provider's request id, usage, and
    finish/status information when the provider returns it, plus
    latency_seconds. The key is never placed in a URL: Gemini
    authenticates with the x-goog-api-key request header, OpenAI
    and Anthropic with their usual authorization headers.
    """
    provider = provider.lower()
    if not messages or not all(
        isinstance(item, dict)
        and item.get("role") in ("user", "assistant")
        and isinstance(item.get("content"), str)
        for item in messages
    ):
        raise ProviderError(
            "messages must be a non-empty list of user/assistant messages"
        )
    started = time.monotonic()
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
                "input": messages,
            },
        )
        parts = []
        for output_item in body.get("output", []):
            for item in output_item.get("content", []):
                if item.get("type") == "output_text" and item.get("text"):
                    parts.append(item["text"])
                elif item.get("type") == "refusal" and item.get("refusal"):
                    parts.append(f"[refusal] {item['refusal']}")
        text = "\n".join(parts)
        metadata = _with_latency(_present({
            "request_id": body.get("id"),
            "status": body.get("status"),
            "usage": body.get("usage"),
            "model": body.get("model"),
        }), started)
        return model, text, metadata
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
                "messages": messages,
            },
        )
        text = "\n".join(
            block.get("text", "")
            for block in body.get("content", [])
            if block.get("type") == "text"
        )
        metadata = _with_latency(_present({
            "request_id": body.get("id"),
            "stop_reason": body.get("stop_reason"),
            "usage": body.get("usage"),
            "model": body.get("model"),
        }), started)
        return model, text, metadata
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
        )
        body = _post(
            url,
            {
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            },
            {
                "contents": [
                    _gemini_content(item) for item in messages
                ]
            },
        )
        text = "\n".join(
            part.get("text", "")
            for candidate in body.get("candidates", [])
            for part in candidate.get("content", {}).get("parts", [])
        )
        candidates = body.get("candidates", [])
        finish = candidates[0].get("finishReason") if candidates else None
        metadata = _with_latency(_present({
            "request_id": body.get("responseId"),
            "model_version": body.get("modelVersion"),
            "usage": body.get("usageMetadata"),
            "finish_reason": finish,
        }), started)
        return model, text, metadata
    raise ProviderError(f"Unsupported provider: {provider}")


def call_provider(provider, prompt, model=None):
    """Call one provider with a single user prompt.

    Thin wrapper over call_provider_messages; returns
    (model, text, metadata) exactly as before.
    """
    return call_provider_messages(
        provider,
        [{"role": "user", "content": prompt}],
        model,
    )
