from scamscript.models import ScriptBreakdown
from scamscript.report import ReportEntry, build_markdown, entries_from_run, rank


def breakdown(score, flags=1, attack="vishing"):
    return ScriptBreakdown(
        attack_type=attack,
        persona="p",
        opening_hook="h",
        trust_building_moves=["a"],
        urgency_tactics=["b"],
        escalation_ladder=["c"],
        target_demographics="d",
        red_flags=[f"flag {i}" for i in range(flags)],
        defense_summary="e",
        sophistication_score=score,
    )


def test_rank_orders_by_score_then_flags():
    low = ReportEntry(name="low", source="low.txt", breakdown=breakdown(2))
    high = ReportEntry(name="high", source="high.txt", breakdown=breakdown(9))
    ties = ReportEntry(name="ties", source="ties.txt", breakdown=breakdown(9, flags=4))
    assert [entry.name for entry in rank([low, ties, high])] == ["ties", "high", "low"]


def test_markdown_has_summary_and_details():
    entries = [
        ReportEntry(name="a.txt", source="/x/a.txt", breakdown=breakdown(9)),
        ReportEntry(name="b.txt", source="/x/b.txt", error="bad json"),
    ]
    markdown = build_markdown(entries, run_id="run-1", command="batch", model="m")
    assert "# Scam script breakdown report" in markdown
    assert "| 1 | a.txt | `vishing` | `other` | 9/10 | 1 | 0 | 1 |" in markdown
    assert "## Failures" in markdown
    assert "bad json" in markdown
    assert "### Defense summary" in markdown
    assert "## Attack types" in markdown
    assert "security research and fraud-awareness" in markdown


def test_markdown_without_successes():
    markdown = build_markdown([ReportEntry(name="b.txt", source="b", error="boom")], run_id="r")
    assert "_No successful analyses in this run._" in markdown
    assert "Mean sophistication" not in markdown


def test_markdown_escapes_pipes():
    entry = ReportEntry(name="a|b.txt", source="x", breakdown=breakdown(5))
    assert "a\\|b.txt" in build_markdown([entry], run_id="r")


def test_entries_from_run_rehydrates_and_skips_corrupt():
    run = {
        "records": [
            {"event": "result", "name": "a", "source": "a", "breakdown": breakdown(7).model_dump()},
            {"event": "result", "name": "b", "source": "b", "breakdown": {"attack_type": "x"}},
            {"event": "result", "name": "c", "source": "c", "breakdown": None, "error": "bad"},
            {"event": "request", "source": "d"},
        ]
    }
    entries = entries_from_run(run)
    assert [entry.ok for entry in entries] == [True, False, False]
    assert entries[1].error == "no breakdown stored"


def test_report_shows_unverified_quotes():
    entry = ReportEntry(
        name="a.txt",
        source="a",
        breakdown=breakdown(5),
        verification={"checked": 2, "verbatim": 1, "missing": 1},
        unverified=[{"field": "red_flags", "quote": "invented", "status": "missing"}],
    )
    markdown = build_markdown([entry], run_id="r")
    assert "Unverified quotes: 1" in markdown
    assert "| 1 |" in markdown and "| 1 |" in markdown
    assert "**Quote check:** 1/2 verbatim, 1 missing" in markdown
    assert "### Unverified quotes" in markdown
    assert "_missing_ [red flags] \"invented\"" in markdown


def test_type_filter_keeps_only_allowed_and_failures():
    entries = [
        ReportEntry(name="a.txt", source="a", breakdown=breakdown(9, attack="vishing"), attack_slug="vishing"),
        ReportEntry(name="b.txt", source="b", breakdown=breakdown(5, attack="romance scam"), attack_slug="romance"),
        ReportEntry(name="bad.txt", source="bad", error="boom"),
    ]
    markdown = build_markdown(entries, run_id="r", only_types={"vishing"})
    assert "a.txt" in markdown
    assert "b.txt" not in markdown
    assert "bad.txt" in markdown


def test_channel_filter():
    entries = [
        ReportEntry(name="a.txt", source="a", breakdown=breakdown(5), channel="vishing"),
        ReportEntry(name="b.txt", source="b", breakdown=breakdown(5), channel="smishing"),
    ]
    markdown = build_markdown(entries, run_id="r", only_channels={"vishing"})
    assert "a.txt" in markdown and "b.txt" not in markdown
