"""Runtime configuration resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

DEFAULT_BASE_URL = "https://api.venice.ai/api/v1"
DEFAULT_MODEL = "deepseek-v4-1-flash-1017-uncensored"
DEFAULT_TIMEOUT = 120.0
ENV_API_KEY = "API_KEY"
ENV_HOME = "SCAMSCRIPT_HOME"


class ConfigError(Exception):
    """Raised when the runtime configuration is unusable."""


@dataclass(slots=True)
class Settings:
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    api_key: str | None = None
    timeout: float = DEFAULT_TIMEOUT
    home: str = field(default_factory=lambda: os.environ.get(ENV_HOME, ""))

    def __post_init__(self) -> None:
        self.base_url = (self.base_url or DEFAULT_BASE_URL).rstrip("/")
        if not self.model:
            self.model = DEFAULT_MODEL
        home = self.home or os.path.join(os.path.expanduser("~"), ".scamscript")
        self.home = home

    def resolve_api_key(self) -> str | None:
        key = self.api_key or os.environ.get(ENV_API_KEY)
        if key is not None:
            key = key.strip()
        return key or None

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
