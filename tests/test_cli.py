import json

import pytest
from typer.testing import CliRunner

from scamscript import cli

runner = CliRunner()


def breakdown(attack="vishing", score=5):
    return {
        "attack_type": attack,
        "persona": "persona text",
        "opening_hook": "hook text",
        "trust_building_moves": ["badge", "case id", "hold music"],
        "urgency_tactics": ["deadline today", "penalty", "supervisor leaves"],
        "escalation_ladder": ["offer deal", "transfer", "warn"],
        "target_demographics": "demographic text",
        "red_flags": ["flag one", "flag two"],
        "defense_summary": "defense text",
        "sophistication_score": score,
    }


class FakeClient:
    replies = {}
    default = None

    def __init__(self, api_key, base_url, model, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.max_tokens = kwargs.get("max_tokens", 4096)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def complete(self, messages, **kwargs):
        prompt = messages[-1]["content"]
        for needle, reply in self.replies.items():
            if needle in prompt:
                return json.dumps(reply)
        return json.dumps(self.default or breakdown())


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SCAMSCRIPT_HOME", str(tmp_path))
    monkeypatch.delenv("API_KEY", raising=False)
    return tmp_path


@pytest.fixture()
def fake(monkeypatch):
    FakeClient.replies = {}
    FakeClient.default = breakdown()
    monkeypatch.setattr(cli, "ChatClient", FakeClient)
    return FakeClient


def test_help_lists_commands(home):
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    for command in ("analyze", "batch", "report", "history"):
        assert command in result.stdout


def test_missing_sources(home):
    result = runner.invoke(cli.app, ["analyze"])
    assert result.exit_code == 1
    assert "pass --file" in result.stdout


def test_file_and_dir_conflict(home, tmp_path):
    result = runner.invoke(cli.app, ["analyze", "--file", "a.txt", "--dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "mutually exclusive" in result.stdout


def test_dry_run_prints_prompt_and_logs(home, tmp_path):
    script = tmp_path / "a.txt"
    script.write_text("CALLER: hello", encoding="utf-8")
    result = runner.invoke(cli.app, ["--dry-run", "analyze", "--file", str(script)])
    assert result.exit_code == 0
    assert "fraud-awareness analyst" in result.stdout
    assert "dry run" in result.stdout
    logs = list((home / "logs").glob("*.jsonl"))
    assert len(logs) == 1
    events = [json.loads(line) for line in logs[0].read_text().splitlines()]
    assert [event["event"] for event in events] == ["run_start", "request", "run_end"]


def test_missing_api_key(home, tmp_path):
    script = tmp_path / "a.txt"
    script.write_text("CALLER: hello", encoding="utf-8")
    result = runner.invoke(cli.app, ["analyze", "--file", str(script)])
    assert result.exit_code == 1
    assert "missing API key" in result.stdout


def test_single_analyze_renders_panel(home, tmp_path, fake):
    script = tmp_path / "a.txt"
    script.write_text("CALLER: hello", encoding="utf-8")
    result = runner.invoke(
        cli.app, ["--api-key", "k", "analyze", "--file", str(script)]
    )
    assert result.exit_code == 0
    for needle in ("ATTACK TYPE", "TRUST BUILDING", "DEFENSE SUMMARY", "defense text"):
        assert needle in result.stdout


def test_batch_ranks_and_writes_report(home, tmp_path, fake):
    (tmp_path / "crude.txt").write_text("CALLER: cheap script", encoding="utf-8")
    (tmp_path / "slick.txt").write_text("CALLER: slick script", encoding="utf-8")
    fake.replies = {"cheap script": breakdown(score=2), "slick script": breakdown(score=9)}
    out = tmp_path / "report.md"
    result = runner.invoke(
        cli.app, ["--api-key", "k", "batch", str(tmp_path), "--output", str(out)]
    )
    assert result.exit_code == 0
    markdown = out.read_text()
    assert markdown.index("| 1 | slick.txt") < markdown.index("| 2 | crude.txt")
    assert "Run summary" in result.stdout


def test_batch_top_limits_report(home, tmp_path, fake):
    (tmp_path / "a.txt").write_text("CALLER: aa", encoding="utf-8")
    (tmp_path / "b.txt").write_text("CALLER: bb", encoding="utf-8")
    fake.replies = {"aa": breakdown(score=1), "bb": breakdown(score=10)}
    out = tmp_path / "r.md"
    result = runner.invoke(
        cli.app, ["--api-key", "k", "batch", str(tmp_path), "--output", str(out), "--top", "1"]
    )
    assert result.exit_code == 0
    markdown = out.read_text()
    assert "b.txt" in markdown
    assert "## 2." not in markdown


def test_failure_exits_nonzero(home, tmp_path, fake):
    (tmp_path / "a.txt").write_text("CALLER: x", encoding="utf-8")
    fake.default = None
    original = FakeClient.complete
    fake.complete = lambda self, messages, **kwargs: "not json"
    result = runner.invoke(cli.app, ["--api-key", "k", "analyze", "--file", str(tmp_path / "a.txt")])
    assert result.exit_code == 1
    assert "FAILED" in result.stdout
    fake.complete = original


def test_report_replays_logged_run(home, tmp_path, fake):
    script = tmp_path / "a.txt"
    script.write_text("CALLER: x", encoding="utf-8")
    runner.invoke(cli.app, ["--api-key", "k", "analyze", "--file", str(script)])

    runs = list((home / "logs").glob("*.jsonl"))
    run_id = runs[0].stem
    result = runner.invoke(cli.app, ["report", "--run-id", run_id])
    assert result.exit_code == 0
    assert "# Scam script breakdown report" in result.stdout
    assert "a.txt" in result.stdout


def test_report_without_runs(home):
    result = runner.invoke(cli.app, ["report"])
    assert result.exit_code == 1
    assert "no logged runs" in result.stdout


def test_report_unknown_run(home):
    result = runner.invoke(cli.app, ["report", "--run-id", "nope"])
    assert result.exit_code == 1
    assert "not found" in result.stdout


def test_history_lists_runs(home, tmp_path):
    script = tmp_path / "a.txt"
    script.write_text("CALLER: x", encoding="utf-8")
    runner.invoke(cli.app, ["--dry-run", "analyze", "--file", str(script)])
    result = runner.invoke(cli.app, ["history"])
    assert result.exit_code == 0
    assert "Previous runs" in result.stdout
    assert "dry-run" in result.stdout
    assert "1 run(s) total" in result.stdout


def test_history_empty(home):
    result = runner.invoke(cli.app, ["history"])
    assert result.exit_code == 0
    assert "no runs logged" in result.stdout


def test_version(home):
    result = runner.invoke(cli.app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "scamscript 0.2.0"


def test_json_output_is_one_object_per_script(home, tmp_path, fake):
    (tmp_path / "a.txt").write_text("CALLER: aa", encoding="utf-8")
    (tmp_path / "b.txt").write_text("CALLER: bb", encoding="utf-8")
    result = runner.invoke(
        cli.app, ["--api-key", "k", "--json", "batch", str(tmp_path)]
    )
    assert result.exit_code == 0
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert [record["event"] for record in records] == ["result", "result", "report"]
    assert all(record["ok"] for record in records[:2])
    assert records[-1]["markdown"].startswith("# Scam script breakdown report")


def test_json_output_writes_report_file(home, tmp_path, fake):
    (tmp_path / "a.txt").write_text("CALLER: aa", encoding="utf-8")
    out = tmp_path / "r.md"
    result = runner.invoke(
        cli.app, ["--api-key", "k", "--json", "batch", str(tmp_path), "--output", str(out)]
    )
    assert result.exit_code == 0
    records = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert records[-1]["path"] == str(out)
    assert "markdown" not in records[-1]
    assert out.is_file()


def test_json_dry_run_emits_prompts(home, tmp_path):
    (tmp_path / "a.txt").write_text("CALLER: ring 415 555 0142", encoding="utf-8")
    result = runner.invoke(
        cli.app, ["--dry-run", "--json", "--redact", "analyze", "--file", str(tmp_path / "a.txt")]
    )
    assert result.exit_code == 0
    record = json.loads(result.stdout.splitlines()[0])
    assert record["event"] == "prompt"
    assert record["redactions"] == {"phone": 1}
    assert "0142" not in record["messages"][-1]["content"]


def test_tuning_flags_reach_client(home, tmp_path, fake, monkeypatch):
    seen = {}
    original = FakeClient.__init__

    def capture(self, api_key, base_url, model, **kwargs):
        seen.update(kwargs)
        original(self, api_key, base_url, model, **kwargs)

    monkeypatch.setattr(FakeClient, "__init__", capture)
    (tmp_path / "a.txt").write_text("CALLER: aa", encoding="utf-8")
    result = runner.invoke(
        cli.app,
        ["--api-key", "k", "--timeout", "9", "--retries", "1", "--max-tokens", "999", "analyze", "--file", str(tmp_path / "a.txt")],
    )
    assert result.exit_code == 0
    assert seen["timeout"] == 9.0
    assert seen["retries"] == 1
    assert seen["max_tokens"] == 999


def test_prune_keeps_newest(home, fake, tmp_path):
    for index in range(3):
        script = tmp_path / f"s{index}.txt"
        script.write_text("CALLER: x", encoding="utf-8")
        runner.invoke(cli.app, ["--dry-run", "analyze", "--file", str(script)])
    result = runner.invoke(cli.app, ["prune", "--keep", "1", "--keep-days", "0"])
    assert result.exit_code == 0
    assert "pruned 2 run(s)" in result.stdout
    assert len(list((home / "logs").glob("*.jsonl"))) == 1


def test_prune_nothing_configured(home):
    result = runner.invoke(cli.app, ["prune", "--keep", "0", "--keep-days", "0"])
    assert result.exit_code == 1
    assert "nothing to do" in result.stdout


def test_strict_quotes_fails_on_invented_quote(home, tmp_path, fake):
    fake.default = breakdown()
    fake.default["opening_hook"] = '"A line nobody said at all"'
    script = tmp_path / "a.txt"
    script.write_text("CALLER: hello there", encoding="utf-8")
    result = runner.invoke(
        cli.app, ["--api-key", "k", "--strict-quotes", "analyze", "--file", str(script)]
    )
    assert result.exit_code == 1
    assert "not found verbatim" in result.stdout


def test_no_verify_skips_quote_check(home, tmp_path, fake):
    fake.default = breakdown()
    fake.default["opening_hook"] = '"A line nobody said at all"'
    script = tmp_path / "a.txt"
    script.write_text("CALLER: hello there", encoding="utf-8")
    result = runner.invoke(
        cli.app, ["--api-key", "k", "--no-verify", "--strict-quotes", "analyze", "--file", str(script)]
    )
    assert result.exit_code == 0
    assert "QUOTE CHECK" not in result.stdout


def test_json_result_carries_verification(home, tmp_path, fake):
    fake.default = breakdown()
    fake.default["opening_hook"] = '"A line nobody said at all"'
    script = tmp_path / "a.txt"
    script.write_text("CALLER: hello there", encoding="utf-8")
    result = runner.invoke(
        cli.app, ["--api-key", "k", "--json", "analyze", "--file", str(script)]
    )
    assert result.exit_code == 0
    record = json.loads(result.stdout.splitlines()[0])
    assert record["verification"] == {"checked": 1, "verbatim": 0, "close": 0, "missing": 1}
    assert record["unverified"][0]["status"] == "missing"
