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
    assert "| 1 | a.txt | vishing | 9/10 | 1 |" in markdown
    assert "## Failures" in markdown
    assert "bad json" in markdown
    assert "### Defense summary" in markdown
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
