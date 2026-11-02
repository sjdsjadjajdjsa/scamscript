"""Minimal OpenAI-compatible chat client."""

from __future__ import annotations

import time
from typing import Any, Callable

import httpx

from scamscript.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
)

BODY_EXCERPT = 400
BACKOFF_BASE = 0.8
BACKOFF_CAP = 8.0
RETRY_AFTER_CAP = 10.0
RETRYABLE_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})

Sleep = Callable[[float], None]


class ClientError(Exception):
    """Raised for transport, protocol, or HTTP failures."""


class TruncatedError(ClientError):
    """Raised when the model stopped because it ran out of output budget."""

    def __init__(self, message: str, partial: str = "") -> None:
        super().__init__(message)
        self.partial = partial


class ChatClient:
    """Thin wrapper around POST /chat/completions with bounded retries."""

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        transport: httpx.BaseTransport | None = None,
        sleep: Sleep = time.sleep,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.retries = max(0, retries)
        self.max_tokens = max_tokens
        self.last_usage: dict[str, int] | None = None
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            transport=transport,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "scamscript/0.2",
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
        max_tokens: int | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens or self.max_tokens,
            "stream": False,
        }

        last: ClientError | None = None
        self.last_usage = None
        for attempt in range(self.retries + 1):
            try:
                body = self._post(payload)
                content, finish_reason, reasoning = _content_of(body)
            except ClientError as exc:
                if not _is_retryable(exc) or attempt == self.retries:
                    raise
                last = exc
                self._sleep(_delay(attempt, exc))
                continue

            usage = body.get("usage") if isinstance(body, dict) else None
            self.last_usage = usage if isinstance(usage, dict) else None
            if finish_reason == "length":
                raise TruncatedError(
                    f"reply hit the {max_tokens or self.max_tokens} token limit before finishing",
                    partial=content or reasoning,
                )
            if not content.strip() and reasoning.strip():
                return reasoning
            return content

        raise last or ClientError("request failed without a response")

    def _post(self, payload: dict[str, Any]) -> Any:
        try:
            response = self._client.post("/chat/completions", json=payload)
        except httpx.HTTPError as exc:
            raise _RetryableError(f"request to {self.endpoint} failed: {exc}") from exc

        if response.status_code >= 400:
            message = (
                f"HTTP {response.status_code} from {self.endpoint}: "
                f"{response.text[:BODY_EXCERPT]}"
            )
            if response.status_code in RETRYABLE_STATUS:
                raise _RetryableError(message, retry_after=_retry_after(response))
            raise ClientError(message)
        try:
            return response.json()
        except ValueError as exc:
            raise ClientError("response body was not JSON") from exc


class _RetryableError(ClientError):
    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _is_retryable(exc: ClientError) -> bool:
    if isinstance(exc, TruncatedError):
        return False
    if isinstance(exc, _RetryableError):
        return True
    return "request to " in str(exc) and "failed:" in str(exc)


def _retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("retry-after")
    if not raw:
        return None
    try:
        return min(float(raw), RETRY_AFTER_CAP)
    except ValueError:
        return None


def _delay(attempt: int, exc: ClientError) -> float:
    if isinstance(exc, _RetryableError) and exc.retry_after is not None:
        return exc.retry_after
    return min(BACKOFF_BASE * (2**attempt), BACKOFF_CAP)


def _content_of(body: Any) -> tuple[str, str | None, str]:
    if not isinstance(body, dict):
        raise ClientError("unexpected response shape")
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ClientError("response contained no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ClientError("unexpected choice shape")
    reason = first.get("finish_reason")
    message = first.get("message")
    reasoning = ""
    if isinstance(message, dict):
        raw_reasoning = message.get("reasoning")
        if isinstance(raw_reasoning, str):
            reasoning = raw_reasoning
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content, reason, reasoning
        if isinstance(content, list):
            parts = [
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
            joined = "".join(parts)
            if joined.strip():
                return joined, reason, reasoning
    text = first.get("text")
    if isinstance(text, str) and text.strip():
        return text, reason, reasoning
    if reasoning.strip():
        return "", reason, reasoning
    raise _RetryableError("response contained no message content")
