"""Content fingerprints for collapsing reprinted scripts."""

from __future__ import annotations

import hashlib
import re

NON_WORD = re.compile(r"[^a-z0-9]+")
HEADER_LINE = re.compile(r"^\s*#")


def body(text: str) -> str:
    """Drop the leading comment block a captured script usually carries."""
    lines = text.splitlines()
    index = 0
    while index < len(lines) and (not lines[index].strip() or HEADER_LINE.match(lines[index])):
        index += 1
    return "\n".join(lines[index:])


def normalize(text: str) -> str:
    lowered = body(text).lower()
    return " ".join(NON_WORD.sub(" ", lowered).split())


def fingerprint(text: str) -> str:
    """Short hash of the normalized body, stable across whitespace and punctuation."""
    normalized = normalize(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
