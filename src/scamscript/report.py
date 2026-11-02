"""Aggregated markdown reporting, live or replayed from logs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from scamscript import taxonomy
from scamscript.models import ScriptBreakdown
from scamscript.store import results_of, utc_now

SECTIONS = (
    ("persona", "Persona adopted"),
    ("opening_hook", "Opening hook"),
    ("trust_building_moves", "Trust-building moves"),
    ("urgency_tactics", "Urgency tactics"),
    ("escalation_ladder", "Escalation ladder"),
    ("target_demographics", "Target demographics"),
    ("red_flags", "Red flags"),
    ("defense_summary", "Defense summary"),
)


@dataclass(slots=True)
class ReportEntry:
    name: str
    source: str
    breakdown: ScriptBreakdown | None = None
    error: str | None = None
    duration: float = 0.0
    skipped: bool = False
    fingerprint: str = ""
    attack_slug: str = ""
    duplicates: list[str] | None = None
    verification: dict[str, int] | None = None
    unverified: list[dict[str, str]] | None = None

    @property
    def ok(self) -> bool:
        return self.breakdown is not None


def entry_from_outcome(outcome: Any) -> ReportEntry:
    return ReportEntry(
        name=outcome.name,
        source=str(getattr(outcome, "source", outcome.name)),
        breakdown=outcome.breakdown,
        skipped=getattr(outcome, "skipped", False),
        fingerprint=getattr(outcome, "fingerprint", ""),
        attack_slug=getattr(outcome, "attack_slug", ""),
        error=outcome.error,
        duration=getattr(outcome, "duration", 0.0),
        verification=getattr(outcome, "verification", None),
        unverified=[
            {"field": issue.field, "quote": issue.quote, "status": issue.status}
            for issue in getattr(outcome, "issues", None) or []
            if not issue.ok
        ],
    )


def entries_from_run(run: dict[str, Any]) -> list[ReportEntry]:
    entries: list[ReportEntry] = []
    for record in results_of(run):
        payload = record.get("breakdown")
        breakdown: ScriptBreakdown | None = None
        if isinstance(payload, dict):
            try:
                breakdown = ScriptBreakdown.model_validate(payload)
            except ValidationError:
                breakdown = None
        entries.append(
            ReportEntry(
                name=record.get("name") or record.get("source") or "unknown",
                source=record.get("source") or "",
                breakdown=breakdown,
                skipped=bool(record.get("skipped")),
                fingerprint=record.get("fingerprint") or "",
                attack_slug=record.get("attack_slug") or "",
                duplicates=record.get("duplicates") or None,
                error=None if breakdown else record.get("error") or "no breakdown stored",
                duration=float(record.get("duration_s") or 0.0),
                verification=record.get("verification") or None,
                unverified=record.get("unverified") or None,
            )
        )
    return entries


def collapse(entries: list[ReportEntry]) -> list[ReportEntry]:
    """Keep the strongest copy of each fingerprint and list the rest under it."""
    groups: dict[str, list[ReportEntry]] = {}
    for entry in entries:
        if entry.ok and entry.fingerprint:
            groups.setdefault(entry.fingerprint, []).append(entry)

    primaries: dict[str, ReportEntry] = {}
    for key, group in groups.items():
        if len(group) > 1:
            best = max(group, key=lambda item: (item.breakdown.sophistication_score, item.breakdown.flag_count))
            best.duplicates = [item.name for item in group if item is not best]
            primaries[key] = best
        else:
            primaries[key] = group[0]

    return [
        primaries[entry.fingerprint] if entry.ok and entry.fingerprint else entry
        for entry in entries
        if not (entry.ok and entry.fingerprint and primaries[entry.fingerprint] is not entry)
    ]


def rank(entries: list[ReportEntry]) -> list[ReportEntry]:
    return sorted(
        entries,
        key=lambda entry: (
            -(entry.breakdown.sophistication_score if entry.breakdown else -1),
            -(entry.breakdown.flag_count if entry.breakdown else 0),
            entry.name.lower(),
        ),
    )


def build_markdown(
    entries: list[ReportEntry],
    run_id: str,
    command: str = "batch",
    model: str | None = None,
    only_types: set[str] | None = None,
) -> str:
    if only_types:
        entries = [
            entry
            for entry in entries
            if not entry.ok or (entry.attack_slug or taxonomy.slugify(entry.breakdown.attack_type)) in only_types
        ]
    ranked = rank(entries)
    ok = [entry for entry in ranked if entry.ok]
    skipped = [entry for entry in ranked if entry.skipped and not entry.ok]
    failed = [entry for entry in ranked if not entry.ok and not entry.skipped]
    average = (
        sum(entry.breakdown.sophistication_score for entry in ok) / len(ok) if ok else 0.0
    )

    lines: list[str] = []
    lines.append("# Scam script breakdown report")
    lines.append("")
    lines.append(f"- Generated: {utc_now()}")
    lines.append(f"- Run: `{run_id}`")
    lines.append(f"- Command: `{command}`")
    if model:
        lines.append(f"- Model: `{model}`")
    lines.append(f"- Scripts analyzed: {len(entries)}")
    lines.append(f"- Successful: {len(ok)}")
    lines.append(f"- Failed: {len(failed)}")
    if skipped:
        lines.append(f"- Skipped at budget: {len(skipped)}")
    folded = sum(len(entry.duplicates or []) for entry in ok)
    if folded:
        lines.append(f"- Duplicate copies folded: {folded}")
    unverified_total = sum(len(entry.unverified or []) for entry in ok)
    if unverified_total:
        lines.append(f"- Unverified quotes: {unverified_total}")
    if ok:
        lines.append(f"- Mean sophistication: {average:.1f}/10")
    lines.append("")

    if ok:
        lines.append("## Attack types")
        lines.append("")
        lines.append("| Type | Scripts | Mean score |")
        lines.append("| --- | ---: | ---: |")
        for slug, count, mean in _type_counts(ok):
            lines.append(f"| {taxonomy.label(slug)} (`{slug}`) | {count} | {mean:.1f} |")
        lines.append("")
        lines.append("## Ranking by sophistication")
        lines.append("")
        lines.append("| Rank | Script | Type | Sophistication | Red flags | Unverified | Copies |")
        lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: |")
        for position, entry in enumerate(ok, start=1):
            lines.append(
                f"| {position} | {_cell(entry.name)} | "
                f"`{entry.attack_slug or taxonomy.slugify(entry.breakdown.attack_type)}` | "
                f"{entry.breakdown.sophistication_score}/10 | {entry.breakdown.flag_count} | "
                f"{len(entry.unverified or [])} | {1 + len(entry.duplicates or [])} |"
            )
        lines.append("")
        for position, entry in enumerate(ok, start=1):
            lines.extend(_detail_section(position, entry))
    else:
        lines.append("_No successful analyses in this run._")
        lines.append("")

    if skipped:
        lines.append("## Skipped")
        lines.append("")
        for entry in skipped:
            lines.append(f"- **{_cell(entry.name)}** (`{_cell(entry.source)}`)")
        lines.append("")

    if failed:
        lines.append("## Failures")
        lines.append("")
        for entry in failed:
            lines.append(f"- **{_cell(entry.name)}** (`{_cell(entry.source)}`): {_cell(entry.error or 'unknown error')}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Generated by scamscript for security research and fraud-awareness training only. "
        "Breakdowns are model-produced readings of captured scripts, not legal advice._"
    )
    lines.append("")
    return "\n".join(lines)


def _detail_section(position: int, entry: ReportEntry) -> list[str]:
    breakdown = entry.breakdown
    assert breakdown is not None
    lines = [f"## {position}. {entry.name}", ""]
    lines.append(f"- **Attack type:** {breakdown.attack_type}")
    lines.append(
        f"- **Type slug:** `{entry.attack_slug or taxonomy.slugify(breakdown.attack_type)}`"
    )
    lines.append(f"- **Sophistication:** {breakdown.sophistication_score}/10")
    lines.append(f"- **Red flags observed:** {breakdown.flag_count}")
    if entry.duplicates:
        lines.append(f"- **Identical copies folded:** {len(entry.duplicates)} ({', '.join(_cell(name) for name in entry.duplicates)})")
    counts = entry.verification or {}
    if counts.get("checked"):
        lines.append(
            f"- **Quote check:** {counts.get('verbatim', 0)}/{counts['checked']} verbatim, "
            f"{counts.get('missing', 0)} missing"
        )
    if entry.source:
        lines.append(f"- **Source:** `{entry.source}`")
    lines.append("")
    if entry.unverified:
        lines.append("### Unverified quotes")
        lines.append("")
        for item in entry.unverified:
            mark = "close" if item.get("status") == "close" else "missing"
            lines.append(f"- _{mark}_ [{(item.get('field') or '').replace('_', ' ')}] \"{item.get('quote', '')}\"")
        lines.append("")
    for field, label in SECTIONS:
        value = getattr(breakdown, field)
        lines.append(f"### {label}")
        lines.append("")
        if isinstance(value, list):
            if value:
                lines.extend(f"{index}. {item}" for index, item in enumerate(value, start=1))
            else:
                lines.append("_None recorded._")
        else:
            lines.append(value or "_None recorded._")
        lines.append("")
    return lines


def _type_counts(entries: list[ReportEntry]) -> list[tuple[str, int, float]]:
    buckets: dict[str, list[int]] = {}
    for entry in entries:
        if not entry.breakdown:
            continue
        slug = entry.attack_slug or taxonomy.slugify(entry.breakdown.attack_type)
        buckets.setdefault(slug, []).append(entry.breakdown.sophistication_score)
    rows = [
        (slug, len(scores), sum(scores) / len(scores))
        for slug, scores in buckets.items()
    ]
    return sorted(rows, key=lambda row: (-row[1], row[0]))


def _cell(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()
