"""Command line interface."""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from scamscript import __version__, brief as briefing, language, prompts, redact, store, taxonomy
from scamscript import report as reporting
from scamscript.analysis import Outcome, analyze_script
from scamscript.client import ChatClient
from scamscript.config import (
    DEFAULT_MAX_TOKENS,
    DEFAULT_RETRIES,
    DEFAULT_TIMEOUT,
    ConfigError,
    Settings,
)
from scamscript.ingest import IngestError, ScriptFile, collect_scripts, read_script
from scamscript.render import (
    render_breakdown,
    render_failure,
    render_prompt,
    render_summary_table,
)
from scamscript.store import RunLogger

DISCLAIMER = (
    "For security research and fraud-awareness training only. "
    "Breakdowns are model-produced readings, not legal advice."
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    help="Reverse-engineer scam call scripts into structured, defensible breakdowns.",
)


@dataclass(slots=True)
class Context:
    settings: Settings
    dry_run: bool
    json_output: bool
    verify_quotes: bool
    strict_quotes: bool
    dedupe: bool
    show_duplicates: bool
    console: Console
    err_console: Console


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"scamscript {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    base_url: str = typer.Option(
        "",
        "--base-url",
        envvar="SCAMSCRIPT_BASE_URL",
        help="OpenAI-compatible API base URL. Falls back to SCAMSCRIPT_BASE_URL.",
    ),
    model: str = typer.Option(
        "",
        "--model",
        "-m",
        envvar="SCAMSCRIPT_MODEL",
        help="Model identifier sent to the API. Falls back to SCAMSCRIPT_MODEL.",
    ),
    api_key: str | None = typer.Option(
        None,
        "--api-key",
        envvar="API_KEY",
        help="API key. Falls back to the API_KEY environment variable.",
    ),
    home: Path | None = typer.Option(
        None,
        "--home",
        envvar="SCAMSCRIPT_HOME",
        help="State directory for logs. Defaults to ~/.scamscript.",
    ),
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT, "--timeout", min=1.0, help="Per-request timeout in seconds."
    ),
    retries: int = typer.Option(
        DEFAULT_RETRIES,
        "--retries",
        min=0,
        max=8,
        help="Retries for transport and rate-limit failures.",
    ),
    max_tokens: int = typer.Option(
        DEFAULT_MAX_TOKENS,
        "--max-tokens",
        min=256,
        help="Output token budget per reply.",
    ),
    concurrency: int = typer.Option(
        1,
        "--concurrency",
        "-j",
        min=1,
        max=16,
        help="Analyze this many scripts in parallel.",
    ),
    max_cost: float | None = typer.Option(
        None,
        "--max-cost",
        min=0.0,
        help="Stop scheduling new scripts once the provider reports this much spend in USD.",
    ),
    redact: bool = typer.Option(
        False,
        "--redact",
        help="Mask likely identifiers before sending and before logging.",
    ),
    lang: str | None = typer.Option(
        None,
        "--language",
        help="Override the detected language code (e.g. en, es) used for the prompt.",
    ),
    verify_quotes: bool = typer.Option(
        True,
        "--verify/--no-verify",
        help="Check quoted claims against the source script.",
    ),
    strict_quotes: bool = typer.Option(
        False,
        "--strict-quotes",
        help="Exit non-zero when a quoted claim is not found in the source.",
    ),
    dedupe: bool = typer.Option(
        True,
        "--dedupe/--no-dedupe",
        help="Fold identical scripts into the strongest copy in reports.",
    ),
    show_duplicates: bool = typer.Option(
        False,
        "--show-duplicates",
        help="Render a full panel for duplicate copies too.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Assemble and print prompts without calling the API.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Emit one JSON object per script on stdout.",
    ),
    no_color: bool = typer.Option(False, "--no-color", help="Disable ANSI colors."),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """Reverse-engineering analyzer for leaked and public scam scripts."""
    settings = Settings(
        base_url=base_url,
        model=model,
        api_key=api_key,
        timeout=timeout,
        retries=retries,
        max_tokens=max_tokens,
        concurrency=concurrency,
        max_cost=max_cost,
        redact=redact,
        language=lang,
        home=str(home) if home else "",
    )
    ctx.obj = Context(
        settings=settings,
        dry_run=dry_run,
        json_output=json_output,
        verify_quotes=verify_quotes,
        strict_quotes=strict_quotes,
        dedupe=dedupe,
        show_duplicates=show_duplicates,
        console=Console(
            no_color=no_color,
            highlight=False,
            soft_wrap=False,
            stderr=json_output,
        ),
        err_console=Console(no_color=no_color, highlight=False, stderr=True),
    )


def _context(ctx: typer.Context) -> Context:
    state = ctx.obj
    if not isinstance(state, Context):
        raise typer.Exit(2)
    return state


def _fail(console: Console, message: str) -> None:
    console.print(f"[bold red]error[/bold red] {message}")
    raise typer.Exit(1)


def _choose_sources(file: Path | None, directory: Path | None, batch: bool) -> bool:
    if file is None and directory is None:
        raise typer.BadParameter("pass --file for one script or --dir for a directory")
    if file is not None and directory is not None:
        raise typer.BadParameter("--file and --dir are mutually exclusive")
    return directory is not None or batch


def _load_sources(
    file: Path | None, directory: Path | None, recursive: bool
) -> list[ScriptFile]:
    if file is not None:
        return [read_script(file)]
    assert directory is not None
    return collect_scripts(directory, recursive=recursive)


def _run(
    state: Context,
    scripts: list[ScriptFile],
    *,
    command: str,
    batch_mode: bool,
    output: Path | None,
    top: int | None,
    types: list[str] | None = None,
    force: bool = False,
) -> None:
    console = state.console
    settings = state.settings
    logger = RunLogger(settings.logs_dir, command)
    logger.run_start(
        model=settings.model,
        base_url=settings.base_url,
        dry_run=state.dry_run,
        command=command,
        sources=[str(script.path) for script in scripts],
    )

    if state.dry_run:
        if not settings.base_url or not settings.model:
            console.print(
                "[yellow]note[/yellow] --base-url and --model are unset; "
                "the prompt below is complete but unaddressed"
            )
        for script in scripts:
            text, counts = _maybe_redact(script.text, settings.redact)
            detected = settings.language or language.detect(text)
            messages = prompts.build_messages(script.name, text, detected)
            logger.request(
                source=str(script.path),
                attempt=1,
                dry_run=True,
                prompt_chars=sum(len(m["content"]) for m in messages),
                redactions=counts,
            )
            if state.json_output:
                _emit_json(
                    {
                        "event": "prompt",
                        "name": script.name,
                        "source": str(script.path),
                        "messages": messages,
                        "redactions": counts,
                    }
                )
            else:
                console.print(render_prompt(script, messages))
        logger.run_end(status="dry-run", results=0, failures=0)
        console.print(f"[dim]dry run logged to {logger.path}[/dim]")
        return

    try:
        settings.require_base_url()
        settings.require_model()
        api_key = settings.require_api_key()
    except ConfigError as exc:
        _fail(console, str(exc))
        return

    outcomes: list[Outcome | None] = [None] * len(scripts)
    report_entries: list[reporting.ReportEntry] = []
    budget = settings.max_cost
    spent = 0.0
    spent_seen = False
    lock = threading.Lock()
    seen: dict[str, str] = {}
    client = ChatClient(
        api_key=api_key,
        base_url=settings.base_url,
        model=settings.model,
        timeout=settings.timeout,
        retries=settings.retries,
        max_tokens=settings.max_tokens,
    )

    def one(script: ScriptFile) -> Outcome:
        nonlocal spent, spent_seen
        if budget is not None:
            with lock:
                blocked = spent >= budget
            if blocked:
                outcome = Outcome(
                    source=script.path,
                    name=script.name,
                    skipped=True,
                    error="skipped: cost budget reached",
                )
                logger.result(**outcome.as_record())
                return outcome
        outcome = analyze_script(
            client,
            script,
            logger,
            redact_identifiers=settings.redact,
            verify_quotes=state.verify_quotes,
            lang=settings.language,
        )
        with lock:
            if state.dedupe and outcome.fingerprint:
                outcome.duplicate_of = seen.setdefault(outcome.fingerprint, outcome.name)
                if outcome.duplicate_of == outcome.name:
                    outcome.duplicate_of = None
        cost = client.last_cost
        if cost:
            with lock:
                spent += cost
                spent_seen = True
        return outcome

    def emit(outcome: Outcome) -> None:
        if state.json_output:
            _emit_json(outcome.as_record())
        elif outcome.skipped:
            console.print(f"[dim]skipped {outcome.name}: budget reached[/dim]")
        elif outcome.duplicate_of and not state.show_duplicates:
            console.print(
                f"[dim]{outcome.name}: duplicate of {outcome.duplicate_of}[/dim]"
            )
        elif outcome.breakdown is not None:
            console.print(
                render_breakdown(
                    outcome.breakdown, outcome.name, outcome.attempts, outcome.issues
                )
            )
        else:
            console.print(
                render_failure(outcome.name, outcome.error or "unknown", outcome.attempts)
            )

    with client:
        if settings.concurrency == 1:
            for index, script in enumerate(scripts, start=1):
                if batch_mode and not state.json_output:
                    console.print(
                        f"[dim]({index}/{len(scripts)}) analyzing {script.name}...[/dim]"
                    )
                outcome = one(script)
                outcomes[index - 1] = outcome
                report_entries.append(reporting.entry_from_outcome(outcome))
                emit(outcome)
        else:
            if not state.json_output:
                console.print(
                    f"[dim]analyzing {len(scripts)} script(s), "
                    f"{settings.concurrency} at a time[/dim]"
                )
            buffered: dict[int, Outcome] = {}
            ready = 0
            with ThreadPoolExecutor(max_workers=settings.concurrency) as pool:
                futures = {
                    pool.submit(one, script): index for index, script in enumerate(scripts)
                }
                for future in as_completed(futures):
                    buffered[futures[future]] = future.result()
                    while ready in buffered:
                        outcome = buffered.pop(ready)
                        outcomes[ready] = outcome
                        report_entries.append(reporting.entry_from_outcome(outcome))
                        emit(outcome)
                        ready += 1

    finished = [outcome for outcome in outcomes if outcome is not None]
    successes = sum(1 for outcome in finished if outcome.ok)
    skipped = sum(1 for outcome in finished if outcome.skipped)
    failures = len(finished) - successes - skipped
    if budget is not None and not spent_seen:
        console.print(
            "[yellow]note[/yellow] the endpoint reported no cost; --max-cost could not be enforced"
        )
    if skipped:
        console.print(f"[yellow]{skipped} script(s) skipped at the cost budget[/yellow]")
    if spent:
        console.print(f"[dim]reported spend: ${spent:.4f}[/dim]")
    unverified = sum(
        1 for outcome in finished for issue in (outcome.issues or []) if not issue.ok
    )
    if state.strict_quotes and unverified:
        failures += 0
    logger.run_end(
        status="ok" if failures == 0 else "partial",
        results=successes,
        failures=failures,
        skipped=skipped,
        cost_usd=round(spent, 6),
    )

    only_types = taxonomy.parse_filter(types)
    if only_types:
        unknown = taxonomy.unknown(types)
        if unknown:
            console.print(
                f"[yellow]note[/yellow] unknown type(s): {', '.join(sorted(unknown))}"
            )
    collapsed = reporting.collapse(report_entries) if state.dedupe else report_entries

    if batch_mode and (successes or skipped):
        if not state.json_output:
            rows = (
                [(e.name, e.breakdown, e.error, e.skipped) for e in collapsed]
                if state.dedupe
                else [(o.name, o.breakdown, o.error, o.skipped) for o in finished]
            )
            console.print(render_summary_table(rows))
        ranked = reporting.rank(collapsed)
        if top:
            ranked = ranked[:top]
        markdown = reporting.build_markdown(
            ranked,
            run_id=logger.run_id,
            command=command,
            model=settings.model,
            only_types=only_types,
        )
        written = _emit_report(
            console, markdown, output, json_mode=state.json_output, force=force
        )
        if state.json_output:
            payload: dict[str, object] = {
                "event": "report",
                "run_id": logger.run_id,
                "path": str(written) if written else None,
            }
            if written is None:
                payload["markdown"] = markdown
            _emit_json(payload)
        console.print(f"[dim]log: {logger.path}[/dim]")

    if unverified and not state.json_output:
        console.print(
            f"[yellow]{unverified} quoted claim(s) not found verbatim in the source[/yellow]"
        )
    if failures:
        raise typer.Exit(1)
    if state.strict_quotes and unverified:
        raise typer.Exit(1)


def _emit_report(
    console: Console,
    markdown: str,
    output: Path | None,
    json_mode: bool = False,
    force: bool = False,
) -> Path | None:
    if output is None:
        if not json_mode:
            typer.echo(markdown)
        return None
    path = output.expanduser()
    if path.exists() and not force:
        _fail(console, f"{path} exists; pass --force to overwrite")
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    except OSError as exc:
        _fail(console, f"cannot write report to {path}: {exc}")
        return None
    console.print(f"[green]report written[/green] {path}")
    return path


def _emit_json(payload: dict[str, object]) -> None:
    typer.echo(json.dumps(payload, ensure_ascii=False))


def _maybe_redact(text: str, enabled: bool) -> tuple[str, dict[str, int]]:
    if not enabled:
        return text, {}
    return redact.redact(text)


@app.command()
def analyze(
    ctx: typer.Context,
    file: Path | None = typer.Option(None, "--file", "-f", help="Path to one script file."),
    directory: Path | None = typer.Option(
        None, "--dir", "-d", help="Directory of script files."
    ),
    batch: bool = typer.Option(
        False, "--batch", help="Treat --dir as a batch and emit an aggregated report."
    ),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write the aggregated markdown report here."
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recurse into subdirectories."),
    top: int | None = typer.Option(None, "--top", min=1, help="Keep only the N most sophisticated scripts."),
    types: list[str] | None = typer.Option(
        None, "--type", help="Only report these type slugs (repeatable or comma-separated)."
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing output file."),
) -> None:
    """Analyze a single script file, or a directory with --batch."""
    state = _context(ctx)
    try:
        batch_mode = _choose_sources(file, directory, batch)
        scripts = _load_sources(file, directory, recursive)
    except typer.BadParameter as exc:
        _fail(state.console, str(exc.message))
        return
    except IngestError as exc:
        _fail(state.console, str(exc))
        return
    _run(
        state,
        scripts,
        command="analyze",
        batch_mode=batch_mode,
        output=output,
        top=top,
        types=types,
        force=force,
    )


@app.command()
def batch(
    ctx: typer.Context,
    directory: Path = typer.Argument(..., help="Directory of script files."),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Write the aggregated markdown report here."
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recurse into subdirectories."),
    top: int | None = typer.Option(None, "--top", min=1, help="Keep only the N most sophisticated scripts."),
    types: list[str] | None = typer.Option(
        None, "--type", help="Only report these type slugs (repeatable or comma-separated)."
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing output file."),
) -> None:
    """Analyze a directory and rank every script by sophistication."""
    state = _context(ctx)
    try:
        scripts = collect_scripts(directory, recursive=recursive)
    except IngestError as exc:
        _fail(state.console, str(exc))
        return
    _run(
        state,
        scripts,
        command="batch",
        batch_mode=True,
        output=output,
        top=top,
        types=types,
        force=force,
    )


@app.command()
def report(  # noqa: A001
    ctx: typer.Context,
    run_id: str | None = typer.Option(
        None, "--run-id", help="Run to replay. Defaults to the newest run with results."
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Write the markdown here."),
    logs_dir: Path | None = typer.Option(None, "--logs-dir", help="Override the log directory."),
    types: list[str] | None = typer.Option(
        None, "--type", help="Only report these type slugs (repeatable or comma-separated)."
    ),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing output file."),
) -> None:
    """Regenerate the aggregated report from a past run's log."""
    state = _context(ctx)
    directory = str(logs_dir.expanduser()) if logs_dir else state.settings.logs_dir

    if run_id is None:
        runs = [run for run in store.discover_runs(directory) if run["results"]]
        if not runs:
            _fail(state.console, f"no logged runs with results in {directory}")
            return
        run = runs[0]
    else:
        run = store.load_run(directory, run_id)
        if run is None:
            _fail(state.console, f"run {run_id} not found in {directory}")
            return

    entries = reporting.entries_from_run(run)
    if not entries:
        _fail(state.console, f"run {run['run_id']} has no stored results")
        return
    markdown = reporting.build_markdown(
        entries,
        run_id=str(run["run_id"]),
        command=str(run.get("command") or "report"),
        model=run.get("model"),
        only_types=taxonomy.parse_filter(types),
    )
    _emit_report(state.console, markdown, output, force=force)


@app.command()
def history(
    ctx: typer.Context,
    limit: int = typer.Option(20, "--limit", "-n", min=1, help="How many runs to list."),
    logs_dir: Path | None = typer.Option(None, "--logs-dir", help="Override the log directory."),
) -> None:
    """List previous runs from the log store."""
    state = _context(ctx)
    directory = str(logs_dir.expanduser()) if logs_dir else state.settings.logs_dir
    runs = store.discover_runs(directory)
    if not runs:
        state.console.print(f"[dim]no runs logged in {directory}[/dim]")
        return

    table = Table(title=f"Previous runs ({directory})", header_style="bold")
    table.add_column("Run")
    table.add_column("Started")
    table.add_column("Command")
    table.add_column("Results", justify="right")
    table.add_column("Failures", justify="right")
    table.add_column("Status")
    for run in runs[:limit]:
        table.add_row(
            str(run["run_id"]),
            str(run["started"] or "-"),
            str(run["command"]),
            str(run["results"]),
            str(run["failures"]),
            str(run["status"]),
        )
    state.console.print(table)
    state.console.print(
        f"[dim]{len(runs)} run(s) total; regenerate one with "
        f"`scamscript report --run-id <id>`[/dim]"
    )


@app.command()
def brief(
    ctx: typer.Context,
    run_id: str | None = typer.Option(
        None, "--run-id", help="Run to brief. Defaults to the newest run with results."
    ),
    types: list[str] | None = typer.Option(
        None, "--type", help="Only brief these type slugs (repeatable or comma-separated)."
    ),
    output: Path | None = typer.Option(None, "--output", "-o", help="Write the briefing here."),
    logs_dir: Path | None = typer.Option(None, "--logs-dir", help="Override the log directory."),
    force: bool = typer.Option(False, "--force", help="Overwrite an existing output file."),
) -> None:
    """Build a one-page defence briefing from a past run."""
    state = _context(ctx)
    directory = str(logs_dir.expanduser()) if logs_dir else state.settings.logs_dir

    if run_id is None:
        runs = [run for run in store.discover_runs(directory) if run["results"]]
        if not runs:
            _fail(state.console, f"no logged runs with results in {directory}")
            return
        run = runs[0]
    else:
        run = store.load_run(directory, run_id)
        if run is None:
            _fail(state.console, f"run {run_id} not found in {directory}")
            return

    entries = reporting.entries_from_run(run)
    markdown = briefing.build_brief(
        entries,
        run_id=str(run["run_id"]),
        only_types=taxonomy.parse_filter(types),
    )
    _emit_report(state.console, markdown, output, force=force)
    if output:
        state.console.print(f"[dim]from run {run['run_id']}[/dim]")


@app.command()
def prune(
    ctx: typer.Context,
    keep_days: int | None = typer.Option(
        30, "--keep-days", min=0, help="Delete runs older than this many days. 0 disables the age rule."
    ),
    keep: int | None = typer.Option(
        200, "--keep", min=0, help="Always keep at least the newest N runs. 0 disables the count rule."
    ),
    logs_dir: Path | None = typer.Option(None, "--logs-dir", help="Override the log directory."),
) -> None:
    """Delete old run logs, keeping the newest runs and recent history."""
    state = _context(ctx)
    if not keep_days and not keep:
        _fail(state.console, "both --keep-days and --keep are 0; nothing to do")
        return
    directory = str(logs_dir.expanduser()) if logs_dir else state.settings.logs_dir
    deleted, freed, kept = store.prune(
        directory,
        keep_days=keep_days or None,
        keep=keep or None,
    )
    state.console.print(
        f"[green]pruned[/green] {deleted} run(s), freed {freed / 1024:.1f} KiB, kept {kept}"
    )


if __name__ == "__main__":
    app()
