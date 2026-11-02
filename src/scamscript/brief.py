"""Turn a recorded run into a one-page defence briefing for trainers."""

from __future__ import annotations

from html import escape

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


def groups_for(
    entries: list[ReportEntry],
    only_types: set[str] | None = None,
    only_channels: set[str] | None = None,
) -> dict[str, list[ReportEntry]]:
    groups: dict[str, list[ReportEntry]] = {}
    for entry in entries:
        if not entry.ok or not entry.breakdown:
            continue
        slug = entry.attack_slug or taxonomy.slugify(entry.breakdown.attack_type)
        if only_types and slug not in only_types:
            continue
        if only_channels and entry.channel not in only_channels:
            continue
        groups.setdefault(slug, []).append(entry)
    return groups


def _parts(group: list[ReportEntry]) -> tuple[list[str], list[str], list[str]]:
    flags = _unique([flag for entry in group for flag in entry.breakdown.red_flags], MAX_FLAGS)
    pressure = _unique(
        [
            item
            for entry in group
            for item in entry.breakdown.urgency_tactics + entry.breakdown.escalation_ladder
        ],
        MAX_PRESSURE,
    )
    counters = _unique([entry.breakdown.defense_summary for entry in group], MAX_COUNTERS)
    return flags, pressure, counters


def build_brief(
    entries: list[ReportEntry],
    run_id: str,
    only_types: set[str] | None = None,
    only_channels: set[str] | None = None,
) -> str:
    groups = groups_for(entries, only_types, only_channels)

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
        flags, pressure, counters = _parts(group)

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


STYLE = """
:root { color-scheme: light dark; }
body { font: 16px/1.55 system-ui, sans-serif; max-width: 46rem; margin: 2rem auto; padding: 0 1rem; }
h1 { font-size: 1.6rem; } h2 { font-size: 1.2rem; margin-top: 2rem; border-top: 1px solid #8884; padding-top: 1rem; }
h3 { font-size: .95rem; text-transform: uppercase; letter-spacing: .04em; margin-bottom: .3rem; }
ul { margin-top: .2rem; } .meta { color: #777; } .slug { font-family: ui-monospace, monospace; color: #777; }
footer { margin-top: 2rem; color: #777; font-size: .85rem; }
"""


def build_brief_html(
    entries: list[ReportEntry],
    run_id: str,
    only_types: set[str] | None = None,
    only_channels: set[str] | None = None,
) -> str:
    groups = groups_for(entries, only_types, only_channels)
    out = [
        "<!DOCTYPE html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Scam defence briefing</title>",
        f"<style>{STYLE}</style></head><body>",
        "<h1>Scam defence briefing</h1>",
        f'<p class="meta">Built from run <code>{escape(run_id)}</code>. '
        "Every claim comes from the analyzed scripts.</p>",
    ]
    if not groups:
        out.append("<p><em>No matching successful analyses in this run.</em></p>")
    else:
        out.append(
            "<p>The flags are what a target can notice. The counters are what to do instead of "
            "complying.</p>"
        )
    for slug, group in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        scores = [entry.breakdown.sophistication_score for entry in group]
        flags, pressure, counters = _parts(group)
        out.append("<section>")
        out.append(
            f"<h2>{escape(taxonomy.label(slug))} <span class=\"slug\">({escape(slug)})</span></h2>"
        )
        out.append(
            f'<p class="meta">{len(group)} script(s), mean sophistication '
            f"{sum(scores) / len(scores):.1f}/10.</p>"
        )
        out.append("<h3>What to notice</h3><ul>")
        out.extend(f"<li>{escape(flag)}</li>" for flag in flags or ["Nothing recorded."])
        out.append("</ul>")
        if pressure:
            out.append("<h3>How pressure is applied</h3><ul>")
            out.extend(f"<li>{escape(item)}</li>" for item in pressure)
            out.append("</ul>")
        out.append("<h3>What to do</h3><ul>")
        out.extend(f"<li>{escape(counter)}</li>" for counter in counters or ["Nothing recorded."])
        out.append("</ul><h3>Sources</h3><ul>")
        out.extend(f"<li><code>{escape(entry.name)}</code></li>" for entry in group)
        out.append("</ul></section>")
    out.append(
        "<footer>Model-produced reading of captured scripts. Security research and "
        "fraud-awareness training only.</footer></body></html>"
    )
    return "\n".join(out) + "\n"
