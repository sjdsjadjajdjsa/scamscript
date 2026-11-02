"""Runtime configuration resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_TIMEOUT = 120.0
DEFAULT_RETRIES = 2
DEFAULT_CONCURRENCY = 1
DEFAULT_MAX_TOKENS = 6144
ENV_API_KEY = "API_KEY"
ENV_HOME = "SCAMSCRIPT_HOME"


class ConfigError(Exception):
    """Raised when the runtime configuration is unusable."""


@dataclass(slots=True)
class Settings:
    base_url: str = ""
    model: str = ""
    api_key: str | None = None
    timeout: float = DEFAULT_TIMEOUT
    retries: int = DEFAULT_RETRIES
    max_tokens: int = DEFAULT_MAX_TOKENS
    redact: bool = False
    language: str | None = None
    concurrency: int = DEFAULT_CONCURRENCY
    max_cost: float | None = None
    home: str = field(default_factory=lambda: os.environ.get(ENV_HOME, ""))

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or "").strip().rstrip("/")
        self.model = (self.model or "").strip()
        self.concurrency = max(1, min(16, self.concurrency))
        if self.max_cost is not None:
            self.max_cost = max(0.0, self.max_cost)
        home = self.home or os.path.join(os.path.expanduser("~"), ".scamscript")
        self.home = home

    def resolve_api_key(self) -> str | None:
        key = self.api_key or os.environ.get(ENV_API_KEY)
        if key is not None:
            key = key.strip()
        return key or None

    def require_base_url(self) -> str:
        if not self.base_url:
            raise ConfigError(
                "missing API base URL: pass --base-url or set the SCAMSCRIPT_BASE_URL "
                "environment variable"
            )
        return self.base_url

    def require_model(self) -> str:
        if not self.model:
            raise ConfigError(
                "missing model: pass --model or set the SCAMSCRIPT_MODEL environment variable"
            )
        return self.model

    def require_api_key(self) -> str:
        key = self.resolve_api_key()
        if key is None:
            raise ConfigError(
                f"missing API key: pass --api-key or set the {ENV_API_KEY} environment variable"
            )
        return key

    @property
    def logs_dir(self) -> str:
        return os.path.join(self.home, "logs")
