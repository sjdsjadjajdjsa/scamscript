# Changelog

All notable changes are recorded here. Versions follow SemVer; the CLI surface and the JSON
schema are the things that count as public API.

## 0.2.0 - 2026-11-02

### Added

- Quote verification: quoted claims in `opening_hook` and `red_flags` are matched against the
  source and marked `close` or `missing`; `--strict-quotes` fails the run, `--no-verify` disables.
- `--json` output (one object per script on stdout), `--timeout`, `--retries`, `--max-tokens`.
- `prune` command and `store.prune` for log retention.
- `--redact` masking of emails, cards, SSNs, phone numbers and long digit runs.
- Adversarial fixture set and `scripts/injection_eval.py` harness.
- `scripts/calibrate.py` for adherence, latency, spread and cost measurement.
- `docs/calibration.md` with three recorded passes and their caveats.
- CI on Python 3.12 and 3.13, issue forms, PR template, code of conduct, citation metadata.

### Changed

- Prompt fences the artifact as untrusted data and states embedded instructions cannot change the
  output format.
- Sophistication anchors widened; 9-10 now reserved for the top decile.
- Reason-only replies: `length` with empty content is truncation, reasoning text is the partial and
  a last-resort fallback.

### Fixed

- Empty content and retryable statuses were treated as fatal; they now back off within `--retries`.
- README, banner and repository metadata rebuilt around scope and evidence.

## 0.1.0 - 2026-11-01

### Added

- First cut: `analyze`, `batch`, `report`, `history`, `--dry-run`, Rich panels, ranked markdown
  reports, Pydantic schema with one repair retry, JSONL logging, three sample transcripts, tests,
  and a pip-installable package with a `scamscript` entry point.
