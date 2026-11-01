# scamscript

`scamscript` is a reverse-engineering analyzer for leaked or public scam call scripts and
vishing transcripts. Point it at a script and it asks a model to take the fraud apart:
who the caller pretends to be, the hook that catches you, how trust is manufactured, what
pressure is applied, what happens when you hesitate, and how to counter that exact
playbook.

## Scope and disclaimer

For security research and fraud-awareness training only. The output is a model-produced
reading of a captured script, not legal advice and not proof of attribution. A script is
evidence of a *pattern*; the live scam that reuses it will differ in details.

## Install

Python 3.12 or newer.

```bash
pip install -e .
```

For tests:

```bash
pip install -e ".[dev]"
```

## Configure

The API key comes from the `API_KEY` environment variable or `--api-key`. The base URL
defaults to Venice's OpenAI-compatible endpoint and the model defaults to
`deepseek-v4-1-flash-1017-uncensored`; both are overridable per invocation.

```bash
export API_KEY=...
```

Any OpenAI-compatible `/chat/completions` server works:

```bash
scamscript --base-url http://localhost:8080/v1 --model local-model analyze --file script.txt
```

## Use

One script:

```bash
scamscript analyze --file examples/gov_impersonation_vishing.txt
```

A directory, ranked into one markdown report:

```bash
scamscript batch examples --output report.md
scamscript analyze --dir examples --batch --top 2
```

See the prompts without spending tokens:

```bash
scamscript --dry-run analyze --file examples/tech_support_scam.txt
```

Replay a past run from the logs, or list runs:

```bash
scamscript history
scamscript report --run-id 20260101T000000Z-abc123def456 --output replayed.md
```

## Output

Each script renders as a panel with colour-coded sections:

| Field | Meaning |
| --- | --- |
| `attack_type` | Fraud family (vishing, smishing, romance, tech support, refund, and so on) |
| `persona` | Identity, authority and tone the caller adopts |
| `opening_hook` | The first line engineered to grab attention |
| `trust_building_moves` | Ordered credibility moves, quoted where possible |
| `urgency_tactics` | Pressure language, deadlines, threats of loss |
| `escalation_ladder` | What the script does when the target hesitates or refuses |
| `target_demographics` | Who the script is written for and why |
| `red_flags` | Observable warning signs in this exact script |
| `defense_summary` | How to recognise and counter this playbook |
| `sophistication_score` | 1-10 complexity estimate used for ranking |

Replies are validated with Pydantic. A malformed reply is retried once with the validation
error and the bad reply fed back as a repair instruction; a second failure is reported
rather than retried indefinitely.

## Logs

Every request appends to a timestamped JSONL file under `~/.scamscript/logs/` (override
with `--home` or `SCAMSCRIPT_HOME`). Prompts, parsed breakdowns, errors, model, base URL
and timing are recorded. The API key is never written. Log files are the source for
`report`, so a run can be regenerated without re-spending tokens.

## Layout

```
src/scamscript/
  cli.py        command wiring, exit codes
  client.py     OpenAI-compatible chat client (httpx)
  analysis.py   per-script loop, one repair retry
  ingest.py     file and directory reading with guards
  models.py     Pydantic schema, tolerant JSON extraction
  prompts.py    analyst system prompt and fix prompt
  render.py     Rich panels, summary table
  report.py     ranked markdown aggregation
  store.py      JSONL run log and run discovery
tests/          parser, validation, client and CLI tests with a mocked transport
examples/       three fictional transcripts
```

## Tests

```bash
pytest
```

The suite mocks the HTTP layer with `httpx.MockTransport`; no network or API key is needed.
