import json
from pathlib import Path

import httpx
import pytest

from scamscript.analysis import analyze_script
from scamscript.client import ChatClient
from scamscript.ingest import ScriptFile
from scamscript.store import RunLogger

VALID = {
    "attack_type": "tech support scam",
    "persona": "fake support agent",
    "opening_hook": "Your machine is broadcasting an error",
    "trust_building_moves": ["free diagnostic", "event viewer proof", "named team"],
    "urgency_tactics": ["drive will fail", "quote expires"],
    "escalation_ladder": ["explain risk", "offer package", "hold quote"],
    "target_demographics": "home users on Windows",
    "red_flags": ["unsolicited call", "remote access"],
    "defense_summary": "Call the vendor's published line",
    "sophistication_score": 6,
}

SCRIPT = ScriptFile(path=Path("/tmp/tech.txt"), text="CALLER: hello", truncated=False)

MESSAGES = [
    {"role": "system", "content": "sys"},
    {"role": "user", "content": "hi"},
]


@pytest.fixture()
def logger(tmp_path):
    return RunLogger(str(tmp_path), "analyze")


def reply(content):
    return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})


def client_for(handler):
    return ChatClient(
        api_key="k",
        base_url="https://example.test/v1",
        retries=0,
        transport=httpx.MockTransport(handler),
        sleep=lambda _: None,
    )


def test_valid_first_attempt(logger):
    with client_for(lambda request: reply(json.dumps(VALID))) as client:
        outcome = analyze_script(client, SCRIPT, logger)
    assert outcome.ok
    assert outcome.attempts == 1
    assert outcome.breakdown.sophistication_score == 6


def test_retries_once_on_malformed_then_succeeds(logger):
    calls = []

    def handler(request):
        calls.append(json.loads(request.read()))
        if len(calls) == 1:
            return reply("sorry, here you go")
        return reply(json.dumps(VALID))

    with client_for(handler) as client:
        outcome = analyze_script(client, SCRIPT, logger)

    assert outcome.ok
    assert outcome.attempts == 2
    assert len(calls) == 2
    fix_messages = calls[1]["messages"]
    assert fix_messages[-2]["role"] == "assistant"
    assert "could not be validated" in fix_messages[-1]["content"]


def test_gives_up_after_single_retry(logger):
    def handler(request):
        return reply("still not json")

    with client_for(handler) as client:
        outcome = analyze_script(client, SCRIPT, logger)

    assert not outcome.ok
    assert outcome.attempts == 2
    assert "invalid model JSON" in outcome.error


def test_http_error_not_retried(logger):
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(500, text="nope")

    with client_for(handler) as client:
        outcome = analyze_script(client, SCRIPT, logger)

    assert not outcome.ok
    assert outcome.attempts == 1
    assert "500" in outcome.error
    assert len(calls) == 1


def test_logger_records_request_result_and_error(tmp_path):
    log = RunLogger(str(tmp_path), "analyze")

    def handler(request):
        return reply("bad")

    with client_for(handler) as client:
        analyze_script(client, SCRIPT, log)

    lines = [json.loads(line) for line in log.path.read_text().splitlines()]
    events = [line["event"] for line in lines]
    assert events.count("request") == 2
    assert events.count("error") == 2
    assert events[-1] == "result"
    assert lines[-1]["breakdown"] is None
    assert all(line["run_id"] == log.run_id for line in lines)
    assert lines[0]["source"] == "/tmp/tech.txt"


def test_truncated_reply_is_repaired(logger):
    calls = []
    truncated = httpx.Response(
        200,
        json={"choices": [{"message": {"content": '{"attack_type"'}, "finish_reason": "length"}]},
    )

    def handler(request):
        calls.append(json.loads(request.read()))
        if len(calls) == 1:
            return truncated
        return reply(json.dumps(VALID))

    with client_for(handler) as client:
        outcome = analyze_script(client, SCRIPT, logger)

    assert outcome.ok
    assert outcome.attempts == 2
    assert "cut off" in calls[1]["messages"][-1]["content"]


def test_truncated_twice_reports_error(logger):
    def handler(request):
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "{"}, "finish_reason": "length"}]},
        )

    with client_for(handler) as client:
        outcome = analyze_script(client, SCRIPT, logger)

    assert not outcome.ok
    assert outcome.attempts == 2
    assert "truncated" in outcome.error


def test_redaction_applied_to_prompt_and_breakdown(logger):
    sent = []

    def handler(request):
        sent.append(json.loads(request.read())["messages"][-1]["content"])
        return reply(json.dumps(VALID))

    script = ScriptFile(path=Path("/tmp/pii.txt"), text="CALLER: ring 415 555 0142")
    with client_for(handler) as client:
        outcome = analyze_script(client, script, logger, redact_identifiers=True)

    assert "0142" not in sent[0]
    assert outcome.redactions == {"phone": 1}


def quoted(**overrides):
    data = dict(VALID)
    data.update(overrides)
    return data


def test_verification_flags_invented_quote(logger):
    script = ScriptFile(path=Path("/tmp/tech.txt"), text="CALLER: hello there", truncated=False)
    payload = quoted(opening_hook='"A line nobody said at all"')
    with client_for(lambda request: reply(json.dumps(payload))) as client:
        outcome = analyze_script(client, script, logger)

    assert outcome.breakdown is not None
    assert outcome.issues and outcome.issues[0].status == "missing"
    assert outcome.as_record()["unverified"][0]["quote"] == "A line nobody said at all"


def test_verification_can_be_disabled(logger):
    script = ScriptFile(path=Path("/tmp/tech.txt"), text="CALLER: hello there", truncated=False)
    payload = quoted(opening_hook='"A line nobody said at all"')
    with client_for(lambda request: reply(json.dumps(payload))) as client:
        outcome = analyze_script(client, script, logger, verify_quotes=False)

    assert outcome.issues is None
    assert outcome.verification is None
