from scamscript.brief import build_brief
from scamscript.models import ScriptBreakdown
from scamscript.report import ReportEntry


def entry(name, attack, flags, counters, score=5, slug=None):
    breakdown = ScriptBreakdown(
        attack_type=attack,
        persona="p",
        opening_hook="h",
        trust_building_moves=["a"],
        urgency_tactics=["deadline today"],
        escalation_ladder=["transfer"],
        target_demographics="d",
        red_flags=flags,
        defense_summary=counters,
        sophistication_score=score,
    )
    return ReportEntry(name=name, source=name, breakdown=breakdown, attack_slug=slug)


def test_brief_groups_and_dedupes():
    entries = [
        entry("a", "tech support scam", ["unsolicited call", "remote access"], "hang up", 6),
        entry("b", "tech support scam", ["Unsolicited call", "fake error"], "Hang up", 8),
        entry("c", "romance scam", ["no video call"], "ask for a live call", 4),
    ]
    out = build_brief(entries, run_id="r1")
    assert out.count("## Tech support") == 1
    assert "unsolicited call" in out
    assert out.lower().count("unsolicited call") == 1
    assert "hang up" in out.lower()
    assert "romance" in out.lower()
    assert "2 script(s), mean sophistication 7.0/10." in out


def test_brief_skips_failed_and_filters_types():
    entries = [
        entry("a", "vishing", ["flag"], "counter"),
        ReportEntry(name="bad", source="bad", error="boom"),
        entry("b", "romance scam", ["flag"], "counter"),
    ]
    out = build_brief(entries, run_id="r", only_types={"vishing"})
    assert "Vishing" in out
    assert "Romance" not in out
    assert "bad" not in out


def test_brief_empty():
    out = build_brief([], run_id="r")
    assert "_No matching successful analyses" in out


def test_brief_caps_list_length():
    flags = [f"flag {i}" for i in range(10)]
    out = build_brief([entry("a", "vishing", flags, "c")], run_id="r")
    assert out.count("- flag ") == 6


def test_html_brief_structure_and_escaping():
    from scamscript.brief import build_brief_html

    out = build_brief_html(
        [entry("a<b>.txt", "vishing", ["<script>alert(1)</script>"], "hang up & verify")], run_id="r"
    )
    assert out.startswith("<!DOCTYPE html>")
    assert "<script>alert(1)</script>" not in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out
    assert "hang up &amp; verify" in out
    assert "<title>Scam defence briefing</title>" in out


def test_html_brief_empty():
    from scamscript.brief import build_brief_html

    assert "No matching successful analyses" in build_brief_html([], run_id="r")
