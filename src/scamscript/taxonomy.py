"""Map free-text attack descriptions onto a fixed set of slugs."""

from __future__ import annotations

import re

OTHER = "other"

# Checked in order: the earlier, more specific family wins.
RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("bec", ("business email", "bec", "invoice fraud", "vendor payment", "mandate fraud", "ceo fraud")),
    ("tech-support", ("tech support", "tech-support", "remote access", "windows security", "computer support")),
    ("gov-impersonation", (
        "government", "tax", "revenue", "irs", "hmrc", "dvla", "council", "police", "court",
        "medicare", "medicaid", "social security", "ssa",
    )),
    ("utility", ("utility", "water board", "energy", "electric", "gas board", "boiler", "home service")),
    ("refund", ("refund", "overpayment", "rebate", "student loan", "debt relief", "interest rate")),
    ("delivery", ("parcel", "delivery", "courier", "postage", "shipping")),
    ("romance", ("romance", "dating", "long con", "long-con", "sweetheart")),
    ("crypto", ("crypto", "bitcoin", "wallet", "token")),
    ("investment", ("investment", "trading", "broker", "forex", "pig butchering")),
    ("smishing", ("smishing", "sms", "text message", "text-message", "whatsapp")),
    ("vishing", ("vishing", "phone call", "cold call", "robocall", "phone")),
)

CHANNELS = ("vishing", "smishing", "email", "other")
CHANNEL_RULES = (
    ("vishing", ("vishing", "call", "phone", "robocall", "cold call", "landline")),
    ("smishing", ("smishing", "sms", "text message", "text-message", "whatsapp")),
    ("email", ("email", "e-mail", "phishing email")),
)

SLUGS = tuple(slug for slug, _ in RULES) + (OTHER,)
NON_WORD = re.compile(r"[^a-z0-9]+")
MATCHERS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (slug, re.compile(r"\b(?:" + "|".join(re.escape(n) for n in needles) + r")\b"))
    for slug, needles in RULES
)


def slugify(attack_type: str) -> str:
    """Return a canonical slug for a model-written attack description."""
    text = NON_WORD.sub(" ", (attack_type or "").lower())
    for slug, pattern in MATCHERS:
        if pattern.search(text):
            return slug
    return OTHER


def channel_of(*texts: str) -> str:
    """Infer the delivery channel when the model did not supply one."""
    text = NON_WORD.sub(" ", " ".join(texts).lower())
    for channel, needles in CHANNEL_RULES:
        if any(re.search(r"\b" + re.escape(n) + r"\b", text) for n in needles):
            return channel
    return "other"


def unknown(values: list[str] | None) -> set[str]:
    """Raw filter tokens that are not a known slug."""
    if not values:
        return set()
    out: set[str] = set()
    for value in values:
        for chunk in value.split(","):
            token = chunk.strip().lower()
            if token and token not in SLUGS:
                out.add(token)
    return out


def label(slug: str) -> str:
    return {
        "bec": "Business email compromise",
        "tech-support": "Tech support",
        "refund": "Refund / debt relief",
        "gov-impersonation": "Government impersonation",
        "utility": "Utility",
        "delivery": "Delivery",
        "crypto": "Crypto",
        "investment": "Investment",
        "romance": "Romance",
        "smishing": "Smishing",
        "vishing": "Vishing",
        "other": "Other",
    }.get(slug, slug)


def parse_filter(values: list[str] | None) -> set[str]:
    """Turn a comma-separated --type option into a slug set."""
    if not values:
        return set()
    out: set[str] = set()
    for value in values:
        for chunk in value.split(","):
            slug = chunk.strip().lower()
            if slug:
                out.add(slugify(slug))
    return out
