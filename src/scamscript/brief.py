"""Turn a recorded run into a one-page defence briefing for trainers."""

from __future__ import annotations

from scamscript import taxonomy
from scamscript.report import ReportEntry

MAX_FLAGS = 6
MAX_PRESSURE = 4
MAX_COUNTERS = 4


def _unique(values: list[str], limit: int) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value.strip())
        if len(out) >= limit:
            break
    return out


def build_brief(
    entries: list[ReportEntry], run_id: str, only_types: set[str] | None = None
) -> str:
    groups: dict[str, list[ReportEntry]] = {}
    for entry in entries:
        if not entry.ok or not entry.breakdown:
            continue
        slug = entry.attack_slug or taxonomy.slugify(entry.breakdown.attack_type)
        if only_types and slug not in only_types:
            continue
        groups.setdefault(slug, []).append(entry)

    lines = ["# Scam defence briefing", ""]
    lines.append(f"Built from run `{run_id}`. Every claim comes from the analyzed scripts.")
    lines.append("")
    if not groups:
        lines.append("_No matching successful analyses in this run._")
        return "\n".join(lines) + "\n"

    lines.append("Use this in order: the flags are what a target can notice, the counters are what")
    lines.append("they should do instead of complying.")
    lines.append("")

    ordered = sorted(groups.items(), key=lambda item: (-len(item[1]), item[0]))
    for slug, group in ordered:
        scores = [entry.breakdown.sophistication_score for entry in group]
        flags = _unique([flag for entry in group for flag in entry.breakdown.red_flags], MAX_FLAGS)
        pressure = _unique(
            [
                item
                for entry in group
                for item in entry.breakdown.urgency_tactics + entry.breakdown.escalation_ladder
            ],
            MAX_PRESSURE,
        )
        counters = _unique(
            [entry.breakdown.defense_summary for entry in group], MAX_COUNTERS
        )

        lines.append(f"## {taxonomy.label(slug)} (`{slug}`)")
        lines.append("")
        lines.append(f"{len(group)} script(s), mean sophistication {sum(scores) / len(scores):.1f}/10.")
        lines.append("")
        lines.append("### What to notice")
        lines.append("")
        lines.extend(f"- {flag}" for flag in flags or ["_Nothing recorded._"])
        lines.append("")
        if pressure:
            lines.append("### How pressure is applied")
            lines.append("")
            lines.extend(f"- {item}" for item in pressure)
            lines.append("")
        lines.append("### What to do")
        lines.append("")
        lines.extend(f"- {counter}" for counter in counters or ["_Nothing recorded._"])
        lines.append("")
        lines.append("### Sources")
        lines.append("")
        lines.extend(f"- `{entry.name}`" for entry in group)
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Model-produced reading of captured scripts, for security research and fraud-awareness "
        "training only._"
    )
    lines.append("")
    return "\n".join(lines)
