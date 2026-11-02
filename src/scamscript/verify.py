"""Check model quotations against the source script."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from scamscript.models import ScriptBreakdown

DOUBLE_QUOTED = r"[\"“”]([^\"“”]{8,400})[\"“”]"
SINGLE_QUOTED = r"(?<![A-Za-z])['‘]([^'‘’]{8,400})['’](?![A-Za-z])"
QUOTE_PATTERN = re.compile(f"{DOUBLE_QUOTED}|{SINGLE_QUOTED}")
WORD = re.compile(r"[a-z0-9]+")
MIN_QUOTE_WORDS = 3
CLOSE_RATIO = 0.75
SPLIT = re.compile(r"\s*(?:;|—|\s-\s|,)\s*")
LONG_QUOTE_WORDS = 22

FIELDS = ("opening_hook", "red_flags")


@dataclass(slots=True)
class Issue:
    field: str
    quote: str
    status: str
    ratio: float = 0.0

    @property
    def ok(self) -> bool:
        return self.status == "verbatim"


def normalize(text: str) -> str:
    lowered = (
        text.lower()
        .replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
    )
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", lowered).split())


def extract_quotes(value: str) -> list[str]:
    quotes = [
        (match.group(1) or match.group(2) or "").strip()
        for match in QUOTE_PATTERN.finditer(value)
    ]
    return [quote for quote in quotes if len(WORD.findall(quote)) >= MIN_QUOTE_WORDS]


def classify(quote: str, source: str) -> tuple[str, float]:
    """Return (status, ratio) for one quote against the source."""
    needle = normalize(quote)
    if not needle:
        return "missing", 0.0
    hay = normalize(source)
    if needle in hay:
        return "verbatim", 1.0

    words = needle.split()
    hay_words = hay.split()
    window = len(words)
    step = max(1, window // 3)
    best = 0.0
    for start in range(0, max(1, len(hay_words) - window + 1), step):
        candidate = " ".join(hay_words[start : start + window])
        ratio = SequenceMatcher(None, needle, candidate).ratio()
        if ratio > best:
            best = ratio
            if best >= 0.97:
                break
    if best >= CLOSE_RATIO:
        return "close", round(best, 3)
    return "missing", round(best, 3)


def verify_breakdown(breakdown: ScriptBreakdown, source: str) -> list[Issue]:
    """Check quoted claims in the hook and red flags. Paraphrase without quotes is skipped."""
    issues: list[Issue] = []
    for field in FIELDS:
        value = getattr(breakdown, field)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if not item:
                continue
            quotes = extract_quotes(item)
            if not quotes and field == "opening_hook" and len(WORD.findall(item)) >= 4:
                quotes = [item]
            for quote in quotes:
                issues.extend(_check_quote(field, quote, source))
    return issues


def _check_quote(field: str, quote: str, source: str) -> list[Issue]:
    """Long quotes drift; check their clauses separately so one clause cannot hide a miss."""
    chunks = [quote]
    if len(quote.split()) > LONG_QUOTE_WORDS:
        split = [chunk for chunk in SPLIT.split(quote) if len(chunk.split()) >= 3]
        if len(split) > 1:
            chunks = split
    out = []
    for chunk in chunks:
        status, ratio = classify(chunk, source)
        out.append(Issue(field=field, quote=chunk.strip(), status=status, ratio=ratio))
    return out


def summarize(issues: list[Issue]) -> dict[str, int]:
    counts = {"checked": len(issues), "verbatim": 0, "close": 0, "missing": 0}
    for issue in issues:
        counts[issue.status] = counts.get(issue.status, 0) + 1
    return counts


def has_problems(issues: list[Issue]) -> bool:
    return any(issue.status != "verbatim" for issue in issues)
