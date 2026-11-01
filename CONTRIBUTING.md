# Contributing

Small project, low ceremony. Two rules: keep tests offline, and treat prompt or schema changes as
behaviour changes.

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Before opening a PR

- `pytest` passes. The suite mocks HTTP with `httpx.MockTransport`; nothing may hit a real network
  or need a key.
- New parser tolerance or validator behaviour comes with a test, including the failure path.
- Additions to the schema touch `models.py`, `prompts.py`, `render.py`, `report.py` and the README
  field list together; a half-wired field is worse than none.
- Keep the CLI contract stable: global flags stay global, exit code 1 means at least one script
  failed, and `--json` output stays one object per line on stdout.

## Prompt and scoring changes

Prompts are code. If you change the analyst instructions or the sophistication anchors, run the
calibration harness against a live endpoint and paste the before/after numbers into the PR:

```bash
API_KEY=... python scripts/calibrate.py --dir examples --repeat 3 \
  --model deepseek/deepseek-v4.1-flash-1017 \
  --base-url https://openrouter.ai/api/v1
```

Reference figures live in `docs/calibration.md`. A change that raises repair rate or drops
first-attempt validity needs a justification beyond "the output reads nicer".

## Samples

`examples/` holds fictional transcripts only. Mark the top of each file as fictional, keep brands
invented, and do not paste victim data that is still under an embargo. If you add a real transcript,
note its provenance in the header comment.

## Style

- Standard library first; new dependencies need a pinned version and a reason.
- Type hints on public functions, `from __future__ import annotations` at the top.
- No comments that restate the code; explain the reason when it is not obvious.
- Keep user-facing strings plain and lowercase for errors, sentence case for help text.

## Commits

One logical change per commit. Subject under 72 characters, imperative mood, body explains why.
Do not commit `.venv/`, logs or keys.
