# Changelog

All notable changes are recorded here. Versions follow SemVer; the CLI surface and the JSON
schema are the things that count as public API.

## Unreleased

## 0.6.0 - 2026-11-02

### Added

- Closed-set attack type slugs, a per-type count and mean score table, and `--type` filtering with an
  unknown-token warning. Raw descriptions are preserved.

### Changed

- Panels show the slug beneath the attack type.

### Security

- Log directories are created `0700` and log files `0600`, so captures are not world-readable.

## 0.5.0 - 2026-11-02

### Added

- Content fingerprints and duplicate folding: reprints collapse to the strongest copy in reports,
  with a folded count and `duplicate_of` in JSON.
- `--dedupe/--no-dedupe` (on by default) and `--show-duplicates` to render every panel.

### Changed

- Duplicate panels are replaced by a one-line pointer unless `--show-duplicates` is set.

## 0.4.1 - 2026-11-02

### Fixed

- README lost the scale and spend section during an earlier edit; restored so the new flags are
  documented where people look.

## 0.4.0 - 2026-11-02

### Added

- `--concurrency N` (1-16) with order-preserving output.
- `--max-cost USD`: stop scheduling once reported spend reaches the cap, mark the rest skipped, and
  warn when a provider reports no cost.
- Per-run reported spend in output and logs.

### Changed

- Token usage is tracked per thread so parallel calls cannot read each other's cost.

## 0.3.0 - 2026-11-02

### Changed

- Breaking: no default provider or model. `--base-url` and `--model` (or `SCAMSCRIPT_BASE_URL` /
  `SCAMSCRIPT_MODEL`) are required for API calls; `--dry-run` works without them.

## 0.2.1 - 2026-11-02

### Fixed

- PyPI project page: absolute image and link URLs so the banner, demo and docs links resolve.
- License metadata now uses the SPDX expression `MIT` plus `license-files` instead of embedding the
  full license text in the sidebar.

### Added

- Terminal demo GIF in the README, recorded against a local stub endpoint.

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
