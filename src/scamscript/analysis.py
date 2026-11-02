"""Single-script analysis loop with one repair retry."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scamscript import dedupe, prompts, redact, verify
from scamscript.client import ChatClient, ClientError, TruncatedError
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
    redactions: dict[str, int] | None = None
    skipped: bool = False
    fingerprint: str = ""
    duplicate_of: str | None = None
    issues: list[verify.Issue] | None = None
    verification: dict[str, int] | None = None

    @property
    def ok(self) -> bool:
        return self.breakdown is not None

    def as_record(self) -> dict[str, Any]:
        return {
            "event": "result",
            "source": str(self.source),
            "name": self.name,
            "ok": self.ok,
            "skipped": self.skipped,
            "fingerprint": self.fingerprint,
            "duplicate_of": self.duplicate_of,
            "attempts": self.attempts,
            "duration_s": round(self.duration, 3),
            "breakdown": self.breakdown.model_dump() if self.breakdown else None,
            "error": self.error,
            "redactions": self.redactions or {},
            "verification": self.verification or {},
            "unverified": [
                {"field": issue.field, "quote": issue.quote, "status": issue.status}
                for issue in self.issues or []
                if not issue.ok
            ],
        }


def analyze_script(
    client: ChatClient,
    script: ScriptFile,
    logger: RunLogger,
    *,
    redact_identifiers: bool = False,
    verify_quotes: bool = True,
) -> Outcome:
    outcome = Outcome(
        source=script.path, name=script.name, fingerprint=dedupe.fingerprint(script.text)
    )
    started = time.monotonic()

    text = script.text
    if redact_identifiers:
        text, counts = redact.redact(text)
        outcome.redactions = counts

    messages = prompts.build_messages(script.name, text)
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
            max_tokens=client.max_tokens,
            redactions=outcome.redactions or {},
        )
        try:
            raw = client.complete(messages)
        except TruncatedError as exc:
            last_error = str(exc)
            outcome.error = f"reply truncated: {last_error}"
            outcome.raw = exc.partial
            logger.error(
                source=str(script.path),
                attempt=attempt,
                error=outcome.error,
                partial=_maybe_redact(exc.partial, redact_identifiers),
            )
            if attempt < MAX_ATTEMPTS:
                messages = prompts.fix_messages(
                    script.name, text, "reply was cut off before the JSON closed", exc.partial
                )
            continue
        except ClientError as exc:
            outcome.error = str(exc)
            logger.error(source=str(script.path), attempt=attempt, error=str(exc))
            break

        outcome.raw = raw
        visible = _maybe_redact(raw, redact_identifiers)
        try:
            outcome.breakdown = parse_breakdown(visible)
            outcome.error = None
            if verify_quotes:
                outcome.issues = verify.verify_breakdown(outcome.breakdown, text)
                outcome.verification = verify.summarize(outcome.issues)
            break
        except BreakdownError as exc:
            last_error = str(exc)
            outcome.error = f"invalid model JSON: {last_error}"
            logger.error(
                source=str(script.path),
                attempt=attempt,
                error=outcome.error,
                raw=visible[:2000],
            )
            if attempt < MAX_ATTEMPTS:
                messages = prompts.fix_messages(script.name, text, last_error, raw)

    outcome.duration = time.monotonic() - started
    logger.result(**outcome.as_record())
    return outcome


def _maybe_redact(text: str, enabled: bool) -> str:
    if not enabled:
        return text
    return redact.redact(text)[0]
