# Real corpus

Ten published transcripts with provenance, under `corpus/real/`. They exist to test what fixtures
cannot: ASR artefacts, 40-minute calls, repeated digits, overlapping speakers, single-message text
lures, and transcripts that are recalled rather than recorded.

| File | Type | Source | Verbatim |
| --- | --- | --- | --- |
| `real-commonwealth-bank-card-vishing.txt` | bank card "verification" | scripts.r00ting.net, 2023-09-10 | yes, timestamped, PII redacted by publisher |
| `real-medicare-benefits-vishing.txt` | Medicare benefits pitch | scripts.r00ting.net, 2023-08-30 | yes, timestamped, PII redacted by publisher |
| `real-credit-union-card-vishing.txt` | card breach verification | Universal 1 Credit Union | recalled by the target |
| `real-ftc-irs-settlement-robocall.txt` | IRS impersonation | U.S. FTC | yes |
| `real-ftc-ssa-suspension-robocall.txt` | SSA suspension | U.S. FTC | yes |
| `real-ftc-apple-support-robocall.txt` | Apple tech support | U.S. FTC | yes |
| `real-ftc-utility-rebate-robocall.txt` | utility rebate | U.S. FTC | yes |
| `real-ftc-student-loan-robocall.txt` | student loan relief | U.S. FTC | yes |
| `real-ftc-interest-rate-robocall.txt` | interest rate reduction | U.S. FTC | yes |
| `real-usps-invalid-zip-smishing.txt` | USPS delivery smishing | Newsweek, 2025-03-06 | yes, single message |

FTC transcripts are U.S. government work. The r00ting transcripts and the Newsweek message are quoted
for research; check the publishers before commercial reuse. Two files are 40k-120k characters, so a
batch over this directory is a real cost and latency test rather than a formality.

## What the first run showed

Ten files, `--concurrency 3 --redact`, 2026-11-02, primary model:

- 10/10 parsed, but two long calls hit the token ceiling on the first attempt and needed the repair
  path. The default output budget is now 6144, up from 4096, because of this.
- Classification was sensible after one fix: the utility-rebate robocall was landing in `refund`
  because the rebate lure outranked the utility claim. Utility is now checked first.
- Quote checking produced three false `missing` verdicts, traced to apostrophes inside words
  (`target's`) being read as quote delimiters. Fixed; the same files re-run clean.
- A compound 30-word quote still reads as `close` rather than verbatim. That is the checker working:
  the model described the pattern instead of quoting a line.

Recorded cost for the full directory: about two cents.

## Channel split, same day

A third run added the `channel` field. All nine call transcripts type as `vishing`; the USPS message
is `delivery` + `smishing` instead of one erasing the other. The Medicare call again needed one
repair, and the bank call produced three paraphrased quotes this time against zero the run before:
quote drift varies by draw, which is why the checker flags rather than rewrites.
