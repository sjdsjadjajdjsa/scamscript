# Calibration run, 2026-11-01

Purpose: check that a real endpoint obeys the schema before trusting the analyzer, and put a
number on the repair retry instead of assuming it.

- Endpoint: `https://openrouter.ai/api/v1`
- Model: `deepseek/deepseek-v4.1-flash-1017`
- Corpus: the three `examples/` transcripts, three repetitions (n=9)
- Settings: defaults (`--max-tokens 4096`, `--retries 2`, `--timeout 120`)

## Results

| Metric | Value |
| --- | ---: |
| Samples | 9 |
| Valid on first attempt | 8 (88.9%) |
| Repaired on retry | 1 |
| Failed outright | 0 |
| Final success | 9 (100%) |
| Mean latency | 18.8 s |
| Prompt tokens | 14,011 |
| Completion tokens | 24,581 |
| Billed cost | $0.0162 |
| Score spread | 6 ×6, 7 ×2, 8 ×1 |

## What the numbers say

- The repair retry earns its keep: the one non-conforming reply was an empty `content` with a
  `stop` finish reason, repaired on the second call. That is why empty content is now retried at
  the transport layer too, not just in the analysis loop.
- No reply hit the token ceiling, but reasoning tokens alone reached ~2,570 on the revenue
  transcript, so 4096 is the practical floor rather than a comfortable default for reasoning
  models.
- Latency is dominated by reasoning time, not transport: the fastest sample was 9.9 s slower than
  any HTTP failure threshold would suggest. Keep `--timeout` generous.
- Scores cluster at 6-7 across all three genres. The rubric anchors are usable but compressed;
  the next pass should widen the 3-4 and 9-10 anchors so a clumsy robocall and a rehearsed
  multi-stage operation separate more sharply.
- Redaction matched the one phone number in the corpus and nothing else, as intended. Names and
  case IDs survived, which is the documented limitation.

Cost of a full re-run on this corpus is under two cents, so calibration is cheap enough to repeat
after every prompt change.

## Reproduction

```bash
API_KEY=... python scripts/calibrate.py --dir examples --repeat 3 \
  --model deepseek/deepseek-v4.1-flash-1017 \
  --base-url https://openrouter.ai/api/v1
```

A redacted batch report from the same run is at `sample-report.md`.
