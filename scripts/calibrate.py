#!/usr/bin/env python
"""Measure schema adherence, repair rate and spend against a real endpoint.

Usage:
    API_KEY=... python scripts/calibrate.py --dir examples --repeat 2

Writes one JSON summary to stdout. Logs land in a temporary directory.
"""

from __future__ import annotations

import json
import statistics
import sys
import tempfile
from pathlib import Path

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scamscript.analysis import analyze_script  # noqa: E402
from scamscript.client import ChatClient  # noqa: E402
from scamscript.config import DEFAULT_MAX_TOKENS, Settings  # noqa: E402
from scamscript.ingest import collect_scripts  # noqa: E402
from scamscript.store import RunLogger  # noqa: E402


def main(
    directory: Path = typer.Option(Path("examples"), "--dir", "-d"),
    repeat: int = typer.Option(2, "--repeat", "-n", min=1),
    model: str = typer.Option("", "--model", "-m", envvar="SCAMSCRIPT_MODEL"),
    base_url: str = typer.Option("", "--base-url", envvar="SCAMSCRIPT_BASE_URL"),
    prompt_price: float = typer.Option(0.035, help="USD per million prompt tokens."),
    completion_price: float = typer.Option(0.5, help="USD per million completion tokens."),
    max_tokens: int = typer.Option(DEFAULT_MAX_TOKENS, "--max-tokens"),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Report the run size without calling the endpoint."
    ),
) -> None:
    settings = Settings(base_url=base_url, model=model, max_tokens=max_tokens)
    scripts = collect_scripts(directory)
    runs = [script for _ in range(repeat) for script in scripts]
    if dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "directory": str(directory),
                    "scripts": len(scripts),
                    "samples": len(runs),
                    "prompt_chars": sum(len(script.text) for script in runs),
                },
                indent=2,
            )
        )
        return

    settings.require_base_url()
    settings.require_model()
    api_key = settings.require_api_key()

    outcomes = []
    prompt_tokens = 0
    completion_tokens = 0
    reported_cost = 0.0

    with tempfile.TemporaryDirectory() as home:
        logger = RunLogger(home, "calibrate")
        logger.run_start(model=model, base_url=base_url, dry_run=False, command="calibrate")
        with ChatClient(
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
        ) as client:
            for index, script in enumerate(runs, start=1):
                print(f"[{index}/{len(runs)}] {script.name}", file=sys.stderr)
                outcome = analyze_script(client, script, logger)
                outcomes.append(outcome)
                usage = client.last_usage or {}
                prompt_tokens += int(usage.get("prompt_tokens") or 0)
                completion_tokens += int(usage.get("completion_tokens") or 0)
                reported_cost += float(usage.get("cost") or 0.0)
        logger.run_end(status="ok", results=sum(1 for o in outcomes if o.ok), failures=0)

    first_attempt = sum(1 for o in outcomes if o.ok and o.attempts == 1)
    repaired = sum(1 for o in outcomes if o.ok and o.attempts > 1)
    failures = sum(1 for o in outcomes if not o.ok)
    scores = [o.breakdown.sophistication_score for o in outcomes if o.breakdown]
    durations = [o.duration for o in outcomes if o.duration]

    summary = {
        "model": model,
        "samples": len(outcomes),
        "first_attempt_valid": first_attempt,
        "repaired": repaired,
        "failed": failures,
        "adherence_rate": round(first_attempt / len(outcomes), 3) if outcomes else 0.0,
        "final_success_rate": round((len(outcomes) - failures) / len(outcomes), 3)
        if outcomes
        else 0.0,
        "mean_latency_s": round(statistics.mean(durations), 2) if durations else 0.0,
        "score_histogram": {score: scores.count(score) for score in sorted(set(scores))},
        "usage": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
        "estimated_cost_usd": round(
            reported_cost
            or (
                prompt_tokens / 1_000_000 * prompt_price
                + completion_tokens / 1_000_000 * completion_price
            ),
            6,
        ),
        "per_sample": [
            {
                "name": outcome.name,
                "ok": outcome.ok,
                "attempts": outcome.attempts,
                "duration_s": round(outcome.duration, 2),
                "score": outcome.breakdown.sophistication_score if outcome.breakdown else None,
                "unverified": sum(1 for issue in outcome.issues or [] if not issue.ok),
                "unverified_close": sum(
                    1 for issue in outcome.issues or [] if issue.status == "close"
                ),
                "unverified_missing": sum(
                    1 for issue in outcome.issues or [] if issue.status == "missing"
                ),
                "error": outcome.error,
            }
            for outcome in outcomes
        ],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    typer.run(main)
