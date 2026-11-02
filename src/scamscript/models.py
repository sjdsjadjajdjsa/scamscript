"""Validated schema for a single script breakdown."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

LIST_FIELDS = (
    "trust_building_moves",
    "urgency_tactics",
    "escalation_ladder",
    "red_flags",
)

TEXT_FIELDS = (
    "attack_type",
    "persona",
    "opening_hook",
    "target_demographics",
    "defense_summary",
)


class BreakdownError(Exception):
    """Raised when a model reply cannot be turned into a ScriptBreakdown."""


class ScriptBreakdown(BaseModel):
    """Structured decomposition of one scam script."""

    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)

    attack_type: str
    channel: str = "other"
    persona: str
    opening_hook: str
    trust_building_moves: list[str]
    urgency_tactics: list[str]
    escalation_ladder: list[str]
    target_demographics: str
    red_flags: list[str]
    defense_summary: str
    sophistication_score: int = Field(default=5)

    @field_validator(*TEXT_FIELDS, mode="before")
    @classmethod
    def _coerce_text(cls, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, (list, tuple)):
            return "; ".join(str(item) for item in value if item is not None)
        return str(value)

    @field_validator(*LIST_FIELDS, mode="before")
    @classmethod
    def _coerce_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            parts = [chunk.strip(" -*\t") for chunk in value.splitlines()]
            return [part for part in parts if part] or ([value.strip()] if value.strip() else [])
        if isinstance(value, dict):
            return [f"{k}: {v}" for k, v in value.items()]
        if isinstance(value, (list, tuple)):
            out: list[str] = []
            for item in value:
                if item is None:
                    continue
                if isinstance(item, (list, tuple)):
                    out.append("; ".join(str(part) for part in item))
                else:
                    text = str(item).strip()
                    if text:
                        out.append(text)
            return out
        return [str(value)]

    @field_validator("channel", mode="before")
    @classmethod
    def _channel(cls, value: Any) -> str:
        text = str(value or "").strip().lower()
        aliases = {
            "call": "vishing",
            "phone": "vishing",
            "voice": "vishing",
            "text": "smishing",
            "sms": "smishing",
            "whatsapp": "smishing",
            "mail": "email",
        }
        text = aliases.get(text, text)
        return text if text in {"vishing", "smishing", "email", "other"} else "other"

    @field_validator("sophistication_score", mode="before")
    @classmethod
    def _coerce_score(cls, value: Any) -> int:
        if value is None or value == "":
            return 5
        if isinstance(value, str):
            text = value.strip()
            if "/" in text:
                text = text.split("/", 1)[0]
            digits = "".join(ch for ch in text if ch.isdigit())
            if digits:
                return int(digits[:2])
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return 5

    @field_validator("sophistication_score")
    @classmethod
    def _clamp_score(cls, value: int) -> int:
        return max(1, min(10, value))

    @property
    def flag_count(self) -> int:
        return len(self.red_flags)


def extract_json_object(raw: str) -> dict[str, Any]:
    """Pull the first plausible JSON object out of a model reply."""
    if raw is None:
        raise BreakdownError("empty model reply")
    text = raw.strip()
    if not text:
        raise BreakdownError("empty model reply")

    fenced = _fenced_payload(text)
    for candidate in (fenced, text):
        if candidate is None:
            continue
        parsed = _try_loads(candidate)
        if parsed is not None:
            return parsed

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        parsed = _try_loads(text[start : end + 1])
        if parsed is not None:
            return parsed
    raise BreakdownError("no JSON object found in model reply")


def parse_breakdown(raw: str) -> ScriptBreakdown:
    payload = extract_json_object(raw)
    try:
        return ScriptBreakdown.model_validate(payload)
    except ValueError as exc:
        raise BreakdownError(str(exc)) from exc


def _fenced_payload(text: str) -> str | None:
    marker = "```"
    if marker not in text:
        return None
    start = text.find(marker)
    body_start = text.find("\n", start)
    if body_start == -1:
        body_start = start + len(marker)
    end = text.find(marker, body_start)
    if end == -1:
        return None
    body = text[body_start:end]
    if not body.strip():
        return None
    return body


def _try_loads(candidate: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return None
    if isinstance(parsed, dict):
        return parsed
    if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict):
        return parsed[0]
    return None


def dumps(breakdown: ScriptBreakdown) -> str:
    return json.dumps(breakdown.model_dump(), indent=2, ensure_ascii=False)
