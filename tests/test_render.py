from rich.console import Console

from scamscript.ingest import ScriptFile
from scamscript.models import ScriptBreakdown
from scamscript.render import (
    attack_color,
    border_for,
    render_breakdown,
    render_failure,
    render_prompt,
    render_summary_table,
)
from pathlib import Path


def breakdown(score=5, attack="vishing", empty=False):
    return ScriptBreakdown(
        attack_type=attack,
        persona="p",
        opening_hook="h",
        trust_building_moves=[] if empty else ["a", "b", "c"],
        urgency_tactics=[] if empty else ["d"],
        escalation_ladder=[] if empty else ["e"],
        target_demographics="f",
        red_flags=[] if empty else ["g", "h"],
        defense_summary="i",
        sophistication_score=score,
    )


def capture(renderable, width=100):
    console = Console(width=width, no_color=True, record=True)
    console.print(renderable)
    return console.export_text()


def test_panel_includes_all_sections():
    text = capture(render_breakdown(breakdown(), "a.txt"))
    for label in ("ATTACK TYPE", "TRUST BUILDING", "ESCALATION LADDER", "DEFENSE SUMMARY"):
        assert label in text
    assert "VISHING" in text
    assert "2 red flags" in text


def test_panel_marks_repaired_attempt():
    assert "repaired on attempt 2" in capture(render_breakdown(breakdown(), "a.txt", attempts=2))


def test_panel_handles_empty_lists():
    assert "(none recorded)" in capture(render_breakdown(breakdown(empty=True), "a.txt"))


def test_border_by_score():
    assert border_for(breakdown(9)) == "red"
    assert border_for(breakdown(6)) == "yellow"
    assert border_for(breakdown(2)) == "green"


def test_attack_color_mapping():
    assert attack_color("tech support scam") == "blue"
    assert attack_color("romance scam") == "bright_magenta"
    assert attack_color("unknown thing") == "red"


def test_failure_panel():
    text = capture(render_failure("a.txt", "http exploded", 2))
    assert "FAILED" in text
    assert "http exploded" in text


def test_prompt_panel():
    script = ScriptFile(path=Path("/tmp/a.txt"), text="CALLER: hi")
    text = capture(render_prompt(script, [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]))
    assert "dry run: a.txt" in text
    assert "<system>" in text


def test_summary_table_row_states():
    text = capture(render_summary_table([("ok.txt", breakdown(), None), ("bad.txt", None, "boom")]))
    assert "ok.txt" in text
    assert "boom" in text


def test_panel_shows_quote_check():
    from scamscript.verify import Issue

    issues = [
        Issue(field="opening_hook", quote="a real line", status="verbatim"),
        Issue(field="red_flags", quote="invented claim", status="missing"),
    ]
    text = capture(render_breakdown(breakdown(), "a.txt", issues=issues))
    assert "QUOTE CHECK" in text
    assert "1/2 quotes verbatim" in text
    assert "invented claim" in text


def test_panel_all_verbatim():
    from scamscript.verify import Issue

    issues = [Issue(field="opening_hook", quote="a real line", status="verbatim")]
    assert "all quoted claims found" in capture(render_breakdown(breakdown(), "a.txt", issues=issues))


def test_panel_without_verification_hides_section():
    assert "QUOTE CHECK" not in capture(render_breakdown(breakdown(), "a.txt"))
