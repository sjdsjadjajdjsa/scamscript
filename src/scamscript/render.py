"""Rich rendering of breakdowns, prompts, and summaries."""

from __future__ import annotations

from rich.console import Group, RenderableType
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from scamscript.ingest import ScriptFile
from scamscript.models import ScriptBreakdown
from scamscript.verify import Issue, summarize

SECTION_LABELS = {
    "persona": "PERSONA",
    "opening_hook": "OPENING HOOK",
    "trust_building_moves": "TRUST BUILDING",
    "urgency_tactics": "URGENCY TACTICS",
    "escalation_ladder": "ESCALATION LADDER",
    "target_demographics": "TARGET DEMOGRAPHICS",
    "red_flags": "RED FLAGS",
    "defense_summary": "DEFENSE SUMMARY",
    "quote_check": "QUOTE CHECK",
}

SECTION_COLORS = {
    "attack_type": "bold white on dark_red",
    "persona": "magenta",
    "opening_hook": "italic cyan",
    "trust_building_moves": "yellow",
    "urgency_tactics": "bold orange3",
    "escalation_ladder": "dark_orange3",
    "target_demographics": "blue",
    "red_flags": "bold red",
    "defense_summary": "bold green",
    "quote_check": "dim white",
}

MARKERS = {
    "trust_building_moves": "•",
    "urgency_tactics": "!",
    "escalation_ladder": "→",
    "red_flags": "✗",
}

ATTACK_COLORS = {
    "vishing": "red",
    "smishing": "magenta",
    "romance": "bright_magenta",
    "tech support": "blue",
    "government": "bright_red",
    "refund": "orange3",
    "crypto": "yellow",
}


def border_for(breakdown: ScriptBreakdown) -> str:
    score = breakdown.sophistication_score
    if score >= 8:
        return "red"
    if score >= 5:
        return "yellow"
    return "green"


def attack_color(attack_type: str) -> str:
    lowered = attack_type.lower()
    for needle, color in ATTACK_COLORS.items():
        if needle in lowered:
            return color
    return "red"


def _heading(breakdown_key: str) -> Text:
    return Text(SECTION_LABELS[breakdown_key], style=SECTION_COLORS[breakdown_key])


def _items(values: list[str], marker: str, color: str) -> Text:
    body = Text()
    for index, value in enumerate(values, start=1):
        prefix = f"{index}." if marker == "→" else marker
        body.append(f"  {prefix} ", style=f"bold {color}")
        body.append(value)
        if index < len(values):
            body.append("\n")
    return body


def _section(key: str, breakdown: ScriptBreakdown) -> list[RenderableType]:
    value = getattr(breakdown, key)
    parts: list[RenderableType] = [_heading(key)]
    if isinstance(value, list):
        if not value:
            parts.append(Text("  (none recorded)", style="dim"))
        else:
            parts.append(_items(value, MARKERS[key], SECTION_COLORS[key]))
    else:
        style = "italic" if key == "opening_hook" else ""
        parts.append(Text(f"  {value}", style=style))
    parts.append(Text(""))
    return parts


def render_breakdown(
    breakdown: ScriptBreakdown,
    name: str,
    attempts: int = 1,
    issues: list[Issue] | None = None,
) -> Panel:
    renderables: list[RenderableType] = []

    attack = Text()
    attack.append("ATTACK TYPE  ", style="dim")
    attack.append(
        f" {breakdown.attack_type.upper()} ",
        style=SECTION_COLORS["attack_type"],
    )
    attack.append("   ")
    attack.append("SOPHISTICATION  ", style="dim")
    attack.append(
        f"{breakdown.sophistication_score}/10",
        style=f"bold {border_for(breakdown)}",
    )
    renderables.append(attack)
    renderables.append(Text(""))

    for key in (
        "persona",
        "opening_hook",
        "trust_building_moves",
        "urgency_tactics",
        "escalation_ladder",
        "target_demographics",
        "red_flags",
    ):
        renderables.extend(_section(key, breakdown))

    if issues is not None:
        renderables.extend(_quote_section(issues))

    renderables.extend(_section("defense_summary", breakdown))

    subtitle_parts = [f"{breakdown.flag_count} red flags"]
    counts = summarize(issues or [])
    if counts["checked"]:
        subtitle_parts.append(f"{counts['verbatim']}/{counts['checked']} quotes verbatim")
        if counts["missing"]:
            subtitle_parts.append(f"{counts['missing']} missing")
    if attempts > 1:
        subtitle_parts.append(f"repaired on attempt {attempts}")
    subtitle = " · ".join(subtitle_parts)

    return Panel(
        Group(*renderables),
        title=f"[bold]{name}[/bold]",
        subtitle=f"[dim]{subtitle}[/dim]",
        border_style=border_for(breakdown),
        padding=(0, 1),
    )


def _quote_section(issues: list[Issue]) -> list[RenderableType]:
    parts: list[RenderableType] = [_heading("quote_check")]
    bad = [issue for issue in issues if not issue.ok]
    if not issues:
        parts.append(Text("  (no quoted claims to check)", style="dim"))
    elif not bad:
        parts.append(Text("  all quoted claims found in the source", style="green"))
    else:
        body = Text()
        for index, issue in enumerate(bad, start=1):
            marker = "≈" if issue.status == "close" else "✗"
            style = "yellow" if issue.status == "close" else "red"
            body.append(f"  {marker} ", style=f"bold {style}")
            body.append(f"{issue.field}: ", style="dim")
            body.append(issue.quote, style=style)
            if index < len(bad):
                body.append("\n")
        parts.append(body)
    parts.append(Text(""))
    return parts


def render_failure(name: str, error: str, attempts: int) -> Panel:
    body = Text()
    body.append("FAILED after ", style="bold red")
    body.append(f"{attempts} attempt(s)\n\n")
    body.append(error, style="red")
    return Panel(body, title=f"[bold]{name}[/bold]", border_style="red", padding=(0, 1))


def render_prompt(source: ScriptFile, messages: list[dict[str, str]]) -> Panel:
    body = Text()
    for message in messages:
        body.append(f"<{message['role']}>\n", style="bold cyan")
        body.append(message["content"] + "\n\n", style="")
    header = Text(
        f"{len(messages)} message(s) · {sum(len(m['content']) for m in messages)} chars",
        style="dim",
    )
    return Panel(
        Group(header, Text(""), body),
        title=f"[bold]dry run: {source.name}[/bold]",
        border_style="cyan",
        padding=(0, 1),
    )


def render_summary_table(
    rows: list[tuple[str, ScriptBreakdown | None, str | None, bool]]
) -> Table:
    table = Table(title="Run summary", header_style="bold", expand=True)
    table.add_column("Script", overflow="fold", ratio=3)
    table.add_column("Attack type", ratio=2)
    table.add_column("Score", justify="right")
    table.add_column("Flags", justify="right")
    table.add_column("Status")
    for name, breakdown, error, skipped in rows:
        if skipped:
            table.add_row(name, "-", "-", "-", "[yellow]skipped[/yellow]")
            continue
        if breakdown is None:
            table.add_row(name, "-", "-", "-", f"[red]{error or 'failed'}[/red]")
            continue
        table.add_row(
            name,
            f"[{attack_color(breakdown.attack_type)}]{breakdown.attack_type}[/]",
            f"{breakdown.sophistication_score}/10",
            str(breakdown.flag_count),
            "[green]ok[/green]",
        )
    return table


def render_report(markdown: str) -> Markdown:
    return Markdown(markdown, hyperlinks=True)
