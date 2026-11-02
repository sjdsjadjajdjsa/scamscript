"""Very small stopword-based language guess."""

from __future__ import annotations

import re

WORD = re.compile(r"[a-zà-ÿ']+")

STOPWORDS: dict[str, frozenset[str]] = {
    "en": frozenset(
        "the and you your have this that with for are was not but from they will can our".split()
    ),
    "es": frozenset(
        "el la los las que y en un una es por con para su se del al como más pero".split()
    ),
    "fr": frozenset(
        "le la les et un une est vous nous pour avec des du au ce qui pas sur mais".split()
    ),
    "de": frozenset(
        "der die das und ist nicht sie wir mit für ein eine auf den dem des zu im".split()
    ),
    "pt": frozenset(
        "o a os as que e um uma é por com para seu se do da ao como mais mas".split()
    ),
    "it": frozenset(
        "il lo la gli le e un una è per con dei del che non si ma come più".split()
    ),
    "nl": frozenset(
        "de het een en is niet van dat die voor met op te zijn u wij maar".split()
    ),
}

MIN_HITS = 6
MARGIN = 1.4


def detect(text: str) -> str:
    """Return a two-letter language code, or 'unknown' when the signal is weak."""
    words = WORD.findall(text.lower())
    if len(words) < 30:
        return "unknown"
    scores = {
        code: sum(1 for word in words if word in stop) for code, stop in STOPWORDS.items()
    }
    ranked = sorted(scores.items(), key=lambda item: -item[1])
    best_code, best = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0
    if best < MIN_HITS or best < second * MARGIN:
        return "unknown"
    return best_code


def instruction(language: str | None) -> str:
    if language and language != "unknown":
        return (
            f"The script is in {language!r}. Keep every field in that language and quote the "
            "original wording."
        )
    return (
        "The script may not be English. Keep every field in the language of the script and quote "
        "the original wording."
    )
