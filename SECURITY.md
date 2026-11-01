# Security policy

## Reporting a problem

Open a private advisory through
[GitHub Security Advisories](https://github.com/sjdsjadjajdjsa/scamscript/security/advisories/new)
for anything that is not a plain bug. Include the version or commit, the command, and the smallest
reproduction you can manage.

Expect an acknowledgement within a week. This is a side project with no bounty.

## What counts

- Prompt injection in a script that escapes the JSON contract or smuggles instructions into the
  logged record.
- Log or report leakage of data the redactor claims to mask.
- Path handling problems in `--file`, `--dir` or `--output` (traversal, symlink surprises,
  clobbering).
- Anything that makes an API key appear in output, logs or a commit.

## What does not

- A model producing a wrong or shallow breakdown. That is a calibration issue, not a
  vulnerability; see `docs/calibration.md`.
- A malicious script that the analyzer does not classify correctly.
- Findings in upstream libraries without a demonstration against this tool.

## Handling keys and data

- The key is read from `API_KEY` or `--api-key` and never written to logs.
- Scripts leave the machine when you run an analysis. With `--redact`, likely identifiers are
  masked first, but redaction is regex-based: names and free-form identifiers still reach the
  provider.
- Logs under `~/.scamscript/logs/` contain model output, which can echo the script. Prune them or
  point `--home` at disposable storage when working with sensitive captures.

## Scope

Supported: the current `master`. There are no backports and no LTS branches. Scripts are treated
as untrusted input; the tool reads them and never executes them.
