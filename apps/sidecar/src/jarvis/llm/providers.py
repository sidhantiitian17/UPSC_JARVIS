from __future__ import annotations

import httpx

from jarvis.llm.config import RoutingConfig
from jarvis.llm.secrets import SecretStore
from jarvis.llm.types import Message, Provider, ProviderError, ProviderResult


def _status_to_kind(status: int) -> str:
    if status == 429:
        return "rate_limit"
    if status in (401, 403):
        return "auth"
    if status >= 500:
        return "unavailable"
    return "bad_request"


def _post(client: httpx.Client, url: str, headers: dict, body: dict, timeout: float) -> dict:
    try:
        resp = client.post(url, headers=headers, json=body, timeout=timeout)
    except httpx.HTTPError as e:  # connection refused, timeouts, TLS ...
        raise ProviderError("unavailable", type(e).__name__) from e
    if resp.status_code >= 400:
        raise ProviderError(_status_to_kind(resp.status_code), f"HTTP {resp.status_code}")
    try:
        return resp.json()
    except ValueError as e:
        raise ProviderError("bad_response", "not JSON") from e


class OpenAICompatProvider:
    """OmniRoute, Ollama (/v1) or any OpenAI-compatible endpoint."""

    def __init__(
        self,
        name: str,
        base_url: str,
        kind: str,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.name, self.kind = name, kind
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._key = api_key
        self._client = client or httpx.Client()

    def complete(
        self, messages: list[Message], *, model: str, json_schema: dict | None = None, timeout: float = 60.0
    ) -> ProviderResult:
        body: dict = {
            "model": model,
            "temperature": 0,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if json_schema is not None:
            body["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self._key}"} if self._key else {}
        data = _post(self._client, self._url, headers, body, timeout)
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError("bad_response", "no choices") from e
        usage = data.get("usage") or {}
        return ProviderResult(text, usage.get("prompt_tokens"), usage.get("completion_tokens"), model)


class GeminiProvider:
    """Google AI Studio (Gemini API) free key. The key travels in a header, never in the URL."""

    def __init__(
        self,
        name: str,
        api_key: str,
        kind: str = "recurring_free",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        client: httpx.Client | None = None,
    ) -> None:
        self.name, self.kind = name, kind
        self._key, self._base = api_key, base_url.rstrip("/")
        self._client = client or httpx.Client()

    def complete(
        self, messages: list[Message], *, model: str, json_schema: dict | None = None, timeout: float = 60.0
    ) -> ProviderResult:
        system = "\n".join(m.content for m in messages if m.role == "system")
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
            if m.role != "system"
        ]
        body: dict = {"contents": contents, "generationConfig": {"temperature": 0}}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if json_schema is not None:
            body["generationConfig"]["responseMimeType"] = "application/json"
        data = _post(
            self._client,
            f"{self._base}/models/{model}:generateContent",
            {"x-goog-api-key": self._key},
            body,
            timeout,
        )
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as e:
            raise ProviderError("bad_response", "no candidates") from e
        usage = data.get("usageMetadata") or {}
        return ProviderResult(text, usage.get("promptTokenCount"), usage.get("candidatesTokenCount"), model)


def build_providers(
    routing: RoutingConfig, secrets: SecretStore, client: httpx.Client | None = None
) -> dict[str, Provider]:
    """Instantiate enabled providers; one whose required API key is missing is simply not built."""
    out: dict[str, Provider] = {}
    for name, spec in routing.providers.items():
        if not spec.is_enabled:
            continue
        key = secrets.get(spec.api_key_secret) if spec.api_key_secret else None
        if spec.api_key_secret and not key:
            continue
        if spec.type == "gemini":
            if not key:
                continue
            out[name] = GeminiProvider(name, key, spec.kind, client=client)
        else:
            if not spec.base_url:
                continue
            out[name] = OpenAICompatProvider(name, spec.base_url, spec.kind, api_key=key, client=client)
    return out
