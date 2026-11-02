# AGENTS.md

`scamscript` is a Python CLI that sends captured scam scripts to an OpenAI-compatible
chat endpoint and turns the model's reply into a validated, comparable breakdown
(attack type, hooks, trust moves, red flags, defence, sophistication score). Scripts are
untrusted data; the tool never executes them.

## Setup and commands

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

Run the tool:

```bash
scamscript --dry-run analyze --file examples/tech_support_scam.txt   # no network, no key
scamscript --base-url URL --model NAME --api-key KEY analyze --file script.txt
```

`pytest` is configured with `testpaths = ["tests"]` and `-q` in `pyproject.toml`. There is no
lint or type-check configuration in the repo, and no Makefile or tox.

Python 3.12+; build backend is hatchling with a src layout. The console script is
`scamscript.cli:app`.

## Offline testing is a hard rule

The suite must never hit the network or need a key, and contributions are expected to keep it
that way:

- HTTP is stubbed with `httpx.MockTransport` (see `tests/test_client.py`).
- CLI tests monkeypatch `cli.ChatClient` with the `FakeClient` in `tests/test_cli.py`, which
  returns canned JSON keyed by a substring of the prompt.
- `SCAMSCRIPT_HOME`, `SCAMSCRIPT_BASE_URL`, `SCAMSCRIPT_MODEL` are set per test; `API_KEY` is
  deleted by the `home` fixture so a real key on the machine cannot leak in.

If you add a code path that can retry or spend, add both the success and failure test.

## Architecture and data flow

```
ingest (suffix/size/race guards, optional redact)
  -> prompts.build_messages (system rules + fenced script + language instruction)
  -> ChatClient.complete (retries, truncation detection)
  -> models.parse_breakdown (tolerant JSON extraction, one repair retry)
  -> verify (quote check) -> render / JSONL / markdown report / brief
```

Module roles:

- `src/scamscript/cli.py` - all commands and flags. Global options live on the single
  `@app.callback()`, not on subcommands.
- `src/scamscript/analysis.py` - per-script loop. `MAX_ATTEMPTS = 2`: exactly one repair retry,
  using `prompts.fix_messages` with the validation error fed back.
- `src/scamscript/client.py` - transport. Retryable statuses are `408, 409, 425, 429, 5xx`;
  `Retry-After` is honoured and capped. `finish_reason: length` raises `TruncatedError` with
  the partial text. Reasoning-only replies fall back to the `reasoning` field.
- `src/scamscript/models.py` - Pydantic schema with tolerant coercion: fences, bare lists,
  `9/10` scores, list-of-lists, dict lists. Extra keys are ignored, scores clamped 1-10.
- `src/scamscript/taxonomy.py` - maps free prose to closed slug sets. `RULES` is order
  sensitive: the first, more specific family wins. Channels are the closed set
  `vishing|smishing|email|other`.
- `src/scamscript/verify.py` - compares quoted claims in `opening_hook` and `red_flags` to the
  source. Statuses are `verbatim`, `close` (paraphrase, ratio >= 0.75) or `missing`. Long
  quotes are split into clauses. Verification annotates, it never drops a finding.
- `src/scamscript/store.py` - append-only JSONL under `~/.scamscript/logs/`
  (`SCAMSCRIPT_HOME`/`--home` override). Directories are `0700`, files `0600`. `report` and
  `brief` replay these logs so a run costs nothing.
- `src/scamscript/report.py` / `brief.py` / `render.py` - markdown aggregation, printable
  handout and HTML, Rich panels.

## Gotchas

- **Adding a schema field means changing five places together**: `models.py`, `prompts.py`,
  `render.py`, `report.py`, and the README field list. `CONTRIBUTING.md` calls a half-wired
  field worse than none. Also cover it in a test.
- The script is wrapped in `<<<SCRIPT name=...>>>` / `<<<END SCRIPT>>>` and the system prompt
  declares everything inside untrusted. `examples/adversarial/` contains scripts that fake
  the fence, dictate a score, or demand prose; the fence protects the schema but not the
  classification. Do not "fix" a case by trusting script text.
- Prompt and rubric edits are behaviour changes. Re-run `scripts/calibrate.py` against a live
  endpoint and record before/after numbers in `docs/calibration.md`; raising the repair rate
  needs justification.
- `dedupe.py` hashes the body with leading header lines stripped (`# ...`). That is why
  `corpus/real/` provenance headers do not break duplicate folding, and why one changed digit
  keeps a copy separate. Dedupe happens after analysis, so duplicates are still paid for.
- Redaction runs before the prompt, before logging, and on returned text. It is regex-based
  and deliberately best effort: names and case IDs survive. Never log the API key.
- `--json` writes one JSON object per script to stdout and moves all Rich output to stderr so
  the stream stays pipeable. Keep that split; tests assert the event sequence.
- Exit code 1 means at least one script failed. `--strict-quotes` exits 1 when a quote is not
  verbatim. `--output` refuses to overwrite without `--force`.
- There is no default provider or model: `--base-url`/`SCAMSCRIPT_BASE_URL` and
  `--model`/`SCAMSCRIPT_MODEL` are both required (except for `--dry-run`).
- The version string lives in three places: `pyproject.toml`, `src/scamscript/__init__.py`,
  and the `User-Agent` in `client.py`. Bump all three and update `tests/test_cli.py`.
- `ingest.py` accepts only `TEXT_SUFFIXES`, silently skips unreadable files in a batch, and
  errors if a file's size/mtime changes mid-read. The recursive walk follows symlinks but
  stops on a loop.
- The cost cap reads `usage.cost` from the provider; it cannot enforce anything on an endpoint
  that omits cost and overshoots by up to the concurrency.

## Style

- Standard library first; new dependencies need a pinned version and a reason.
- `from __future__ import annotations` at the top; type hints on public functions.
- Absolute `from scamscript import ...` imports.
- Errors are plain lowercase; help text is sentence case. No comments that restate code.
- One logical change per commit; imperative subject under 72 characters.

## Data directories

- `examples/` - fictional transcripts, invented brands. `examples/adversarial/` is the
  injection set and its own harness is `scripts/injection_eval.py`.
- `corpus/real/` - ten published transcripts; each header carries source, date and verbatim
  status, and `docs/real-corpus.md` tracks provenance. Keep headers on new captures so dedupe
  still works.
- `docs/` - calibration record, sample report and briefing. `docs/sample-report.md` and
  `docs/sample-briefing.html` are generated artifacts; regenerate rather than hand-edit.

To regenerate the samples without spend, run `scripts/rebuild_samples.sh`. It serves the recorded
replies in `scripts/sample_responses.json` through `scripts/stub_endpoint.py`, replays the batch and
the briefing, and rewrites the stored absolute source paths. Both files are hand-maintained copies
of model output, so editing the response JSON changes what the samples show. Keep the README
disclosure that the samples replay a recorded run through a stub.

## CI and release

`.github/workflows/ci.yml` runs `pytest`, a wheel build and `python -m scamscript --version`
on Python 3.12 and 3.13. Release is tag-driven (`v*`) or manual dispatch: build, `twine check`,
install the wheel in a clean venv, then publish to PyPI via OIDC. Never push tags casually.
