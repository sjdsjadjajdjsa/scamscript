"""Minimal OpenAI-compatible chat client."""

from __future__ import annotations

from typing import Any

import httpx

from scamscript.config import DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_TIMEOUT

BODY_EXCERPT = 400


class ClientError(Exception):
    """Raised for transport, protocol, or HTTP failures."""


class ChatClient:
    """Thin wrapper around POST /chat/completions."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            transport=transport,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "scamscript/0.1",
            },
        )

    def __enter__(self) -> "ChatClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/chat/completions"

    def complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2048,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            response = self._client.post("/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            raise ClientError(f"request to {self.endpoint} failed: {exc}") from exc

        if response.status_code >= 400:
            raise ClientError(
                f"HTTP {response.status_code} from {self.endpoint}: "
                f"{response.text[:BODY_EXCERPT]}"
            )
        try:
            body = response.json()
        except ValueError as exc:
            raise ClientError("response body was not JSON") from exc
        return _content_of(body)


def _content_of(body: Any) -> str:
    if not isinstance(body, dict):
        raise ClientError("unexpected response shape")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ClientError("response contained no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ClientError("unexpected choice shape")
    message = first.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            joined = "".join(parts)
            if joined.strip():
                return joined
    text = first.get("text")
    if isinstance(text, str):
        return text
    raise ClientError("response contained no message content")
