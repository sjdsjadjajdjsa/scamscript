"""Single-script analysis loop with one repair retry."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scamscript import prompts
from scamscript.client import ChatClient, ClientError
from scamscript.ingest import ScriptFile
from scamscript.models import BreakdownError, ScriptBreakdown, parse_breakdown
from scamscript.store import RunLogger

MAX_ATTEMPTS = 2


@dataclass(slots=True)
class Outcome:
    source: Path
    name: str
    breakdown: ScriptBreakdown | None = None
    raw: str = ""
    attempts: int = 0
    error: str | None = None
    duration: float = 0.0

    @property
    def ok(self) -> bool:
        return self.breakdown is not None

    def as_record(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "name": self.name,
            "ok": self.ok,
            "attempts": self.attempts,
            "duration_s": round(self.duration, 3),
            "breakdown": self.breakdown.model_dump() if self.breakdown else None,
            "error": self.error,
        }


def analyze_script(client: ChatClient, script: ScriptFile, logger: RunLogger) -> Outcome:
    outcome = Outcome(source=script.path, name=script.name)
    started = time.monotonic()
    messages = prompts.build_messages(script.name, script.text)
    last_error = ""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        outcome.attempts = attempt
        logger.request(
            source=str(script.path),
            attempt=attempt,
            model=client.model,
            base_url=client.base_url,
            message_count=len(messages),
            prompt_chars=sum(len(m["content"]) for m in messages),
        )
        try:
            raw = client.complete(messages)
        except ClientError as exc:
            outcome.error = str(exc)
            logger.error(source=str(script.path), attempt=attempt, error=str(exc))
            break

        outcome.raw = raw
        try:
            outcome.breakdown = parse_breakdown(raw)
            outcome.error = None
            break
        except BreakdownError as exc:
            last_error = str(exc)
            outcome.error = f"invalid model JSON: {last_error}"
            logger.error(
                source=str(script.path),
                attempt=attempt,
                error=outcome.error,
                raw=raw[:2000],
            )
            if attempt < MAX_ATTEMPTS:
                messages = prompts.fix_messages(script.name, script.text, last_error, raw)

    outcome.duration = time.monotonic() - started
    logger.result(**outcome.as_record())
    return outcome
