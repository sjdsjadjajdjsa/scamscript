import pytest

from scamscript.models import ScriptBreakdown
from scamscript.verify import classify, extract_quotes, has_problems, summarize, verify_breakdown

SOURCE = (
    "CALLER: Good afternoon, this is Officer Whitfield. Am I speaking with Mr. Reyes?\n"
    "CALLER: Your account is being suspended today unless you verify the balance.\n"
)


def breakdown(**overrides):
    data = {
        "attack_type": "vishing",
        "persona": "officer",
        "opening_hook": '"Am I speaking with Mr. Reyes?"',
        "trust_building_moves": ["badge"],
        "urgency_tactics": ["today"],
        "escalation_ladder": ["a", "b", "c"],
        "target_demographics": "homeowners",
        "red_flags": ['"Your account is being suspended"', "no paper trail"],
        "defense_summary": "verify",
        "sophistication_score": 5,
    }
    data.update(overrides)
    return ScriptBreakdown(**data)


@pytest.mark.parametrize(
    "quote,status",
    [
        ("Am I speaking with Mr. Reyes?", "verbatim"),
        ("am i speaking with mr reyes", "verbatim"),
        ("Am I speaking with Mister Reyes", "close"),
        ("Entirely made up sentence about things", "missing"),
    ],
)
def test_classify(quote, status):
    assert classify(quote, SOURCE)[0] == status


def test_classify_case_and_punctuation_insensitive():
    assert classify("YOUR ACCOUNT is being suspended!", SOURCE)[0] == "verbatim"


def test_extract_quotes_needs_enough_words():
    assert extract_quotes('"short one" and "a much longer quoted claim"') == [
        "a much longer quoted claim"
    ]


def test_unquoted_hook_still_checked():
    issues = verify_breakdown(breakdown(opening_hook="Am I speaking with Mr. Reyes?"), SOURCE)
    assert [issue.status for issue in issues] == ["verbatim", "verbatim"]


def test_unquoted_red_flag_skipped():
    issues = verify_breakdown(breakdown(red_flags=["no paper trail"]), SOURCE)
    assert all(issue.field == "opening_hook" for issue in issues)


def test_missing_quote_flagged():
    issues = verify_breakdown(breakdown(opening_hook='"A line that is not in the script"'), SOURCE)
    assert issues[0].status == "missing"
    assert has_problems(issues)


def test_clean_breakdown_has_no_problems():
    issues = verify_breakdown(breakdown(), SOURCE)
    assert not has_problems(issues)
    assert summarize(issues) == {"checked": 2, "verbatim": 2, "close": 0, "missing": 0}


def test_all_verbatim_summary():
    assert summarize(verify_breakdown(breakdown(), SOURCE))["missing"] == 0
