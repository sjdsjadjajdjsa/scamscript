from pathlib import Path

from scamscript.dedupe import fingerprint, normalize
from scamscript.report import ReportEntry, collapse

FIXTURES = Path(__file__).parent / "fixtures" / "reprints"


def read(name):
    return (FIXTURES / name).read_text()


def test_header_and_punctuation_ignored():
    assert fingerprint(read("original.txt")) == fingerprint(read("copy-punctuation.txt"))
    assert fingerprint(read("original.txt")) == fingerprint(read("copy-header.txt"))


def test_near_twin_differs():
    assert fingerprint(read("original.txt")) != fingerprint(read("near-twin.txt"))


def test_normalize_collapses_whitespace():
    assert normalize("a  b\n\tc") == "a b c"


def test_empty_and_header_only_stable():
    assert fingerprint("") == fingerprint("# only a header\n")


def entry(name, score, fp="abc"):
    from scamscript.models import ScriptBreakdown

    breakdown = ScriptBreakdown(
        attack_type="vishing",
        persona="p",
        opening_hook="h",
        trust_building_moves=["a"],
        urgency_tactics=["b"],
        escalation_ladder=["c"],
        target_demographics="d",
        red_flags=["e"],
        defense_summary="f",
        sophistication_score=score,
    )
    return ReportEntry(name=name, source=name, breakdown=breakdown, fingerprint=fp)


def test_collapse_keeps_strongest_and_lists_rest():
    entries = [entry("a", 4), entry("b", 9), entry("c", 6)]
    collapsed = collapse(entries)
    assert len(collapsed) == 1
    assert collapsed[0].name == "b"
    assert collapsed[0].duplicates == ["a", "c"]


def test_collapse_leaves_distinct_and_failed_alone():
    entries = [entry("a", 5), entry("twin", 8, fp="zzz"), ReportEntry(name="bad", source="bad")]
    collapsed = collapse(entries)
    assert [item.name for item in collapsed] == ["a", "twin", "bad"]
    assert collapsed[0].duplicates is None
