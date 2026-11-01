"""Best-effort redaction of likely victim identifiers."""

from __future__ import annotations

import re

EMAIL = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*(@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
SSN = re.compile(r"\b\d{3}-\d{2}-(\d{4})\b")
PHONE = re.compile(
    r"(?<![\d+])(?:\+\d{1,3}[ .-]?)?(?:\(\d{1,4}\)[ .-]?)?"
    r"\d{2,4}[ .-]\d{3,4}[ .-]?\d{3,4}(?!\d)"
)
LONG_DIGITS = re.compile(r"\b\d{9,}\b")

RULES = (
    ("email", EMAIL),
    ("card", CARD),
    ("ssn", SSN),
    ("phone", PHONE),
    ("digits", LONG_DIGITS),
)


def _mask(value: str, keep: int = 4) -> str:
    digits = value.strip()
    if len(digits) <= keep:
        return "*" * len(digits)
    return "*" * (len(digits) - keep) + digits[-keep:]


def redact(text: str) -> tuple[str, dict[str, int]]:
    """Mask emails, card numbers, SSNs, phone numbers and long digit runs."""
    counts: dict[str, int] = {}

    def record(kind: str, amount: int = 1) -> None:
        counts[kind] = counts.get(kind, 0) + amount

    text, hits = EMAIL.subn(
        lambda match: f"{match.group(1)}***{match.group(2)}", text
    )
    record("email", hits)

    text, hits = CARD.subn(lambda match: _mask(re.sub(r"[ -]", "", match.group(0))), text)
    record("card", hits)

    text, hits = SSN.subn(lambda match: f"***-**-{match.group(1)}", text)
    record("ssn", hits)

    text, hits = PHONE.subn(lambda match: _mask(re.sub(r"[ .-]", "", match.group(0)), 2), text)
    record("phone", hits)

    text, hits = LONG_DIGITS.subn(lambda match: _mask(match.group(0)), text)
    record("digits", hits)

    return text, {kind: amount for kind, amount in counts.items() if amount}


def describe(counts: dict[str, int]) -> str:
    if not counts:
        return "no identifiers matched"
    return ", ".join(f"{kind}={amount}" for kind, amount in sorted(counts.items()))
