import json

import pytest

VALID = {
    "attack_type": "vishing",
    "persona": "fake revenue officer",
    "opening_hook": "Am I speaking with Mr. Reyes?",
    "trust_building_moves": ["badge number", "case reference", "hold music"],
    "urgency_tactics": ["levy in 48 hours", "penalty of 22 percent", "supervisor leaves at 5"],
    "escalation_ladder": ["offer settlement", "transfer to desk", "warn levy continues"],
    "target_demographics": "older homeowners who answer landlines",
    "red_flags": ["callback number not on card", "deadline today"],
    "defense_summary": "Hang up and dial the published number",
    "sophistication_score": 8,
}


def payload(**overrides):
    data = dict(VALID)
    data.update(overrides)
    return data


@pytest.mark.parametrize(
    "wrapper",
    [
        lambda body: json.dumps(body),
        lambda body: "```json\n" + json.dumps(body) + "\n```",
        lambda body: "Here is the breakdown:\n" + json.dumps(body) + "\nDone.",
        lambda body: json.dumps(body, indent=2),
    ],
)
def test_parses_common_reply_shapes(wrapper):
    from scamscript.models import parse_breakdown

    result = parse_breakdown(wrapper(payload()))
    assert result.attack_type == "vishing"
    assert result.sophistication_score == 8
    assert len(result.red_flags) == 2


def test_first_object_wins_in_array_wrapper():
    from scamscript.models import parse_breakdown

    raw = json.dumps([payload()])
    assert parse_breakdown(raw).attack_type == "vishing"


def test_coerces_string_lists_and_text():
    from scamscript.models import parse_breakdown

    result = parse_breakdown(
        json.dumps(
            payload(
                attack_type=["vishing", "government"],
                trust_building_moves="- badge\n- case id\n- hold music",
                red_flags="callback number\nno paper trail",
                urgency_tactics={"deadline": "48 hours"},
            )
        )
    )
    assert result.attack_type == "vishing; government"
    assert result.trust_building_moves == ["badge", "case id", "hold music"]
    assert result.red_flags == ["callback number", "no paper trail"]
    assert result.urgency_tactics == ["deadline: 48 hours"]


def test_score_from_string_and_clamped():
    from scamscript.models import parse_breakdown

    assert parse_breakdown(json.dumps(payload(sophistication_score="9/10"))).sophistication_score == 9
    assert parse_breakdown(json.dumps(payload(sophistication_score=None))).sophistication_score == 5
    assert parse_breakdown(json.dumps(payload(sophistication_score=42))).sophistication_score == 10


def test_missing_field_rejected():
    from scamscript.models import BreakdownError, parse_breakdown

    data = payload()
    del data["defense_summary"]
    with pytest.raises(BreakdownError) as excinfo:
        parse_breakdown(json.dumps(data))
    assert "defense_summary" in str(excinfo.value)


@pytest.mark.parametrize("raw", ["", "   ", "no json here", "{broken", "[1, 2, 3]"])
def test_non_json_rejected(raw):
    from scamscript.models import BreakdownError, parse_breakdown

    with pytest.raises(BreakdownError):
        parse_breakdown(raw)


def test_extra_keys_ignored():
    from scamscript.models import parse_breakdown

    assert parse_breakdown(json.dumps(payload(noise="ignored"))).persona


def test_flag_count():
    from scamscript.models import parse_breakdown

    assert parse_breakdown(json.dumps(payload())).flag_count == 2
