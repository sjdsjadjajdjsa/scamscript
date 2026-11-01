"""Append-only JSONL request log under the scamscript home."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RUN_ID_LENGTH = 12


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{uuid.uuid4().hex[:RUN_ID_LENGTH]}"


class RunLogger:
    """Writes one JSONL file per run; never raises on log failure."""

    def __init__(self, logs_dir: str, command: str, run_id: str | None = None) -> None:
        self.run_id = run_id or new_run_id()
        self.logs_dir = Path(logs_dir)
        self.command = command
        self.path = self.logs_dir / f"{self.run_id}.jsonl"
        self._started = False

    def _write(self, record: dict[str, Any]) -> None:
        record.setdefault("ts", utc_now())
        record.setdefault("run_id", self.run_id)
        try:
            self.logs_dir.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def run_start(self, **fields: Any) -> None:
        if self._started:
            return
        self._started = True
        self._write({"event": "run_start", "command": self.command, **fields})

    def request(self, **fields: Any) -> None:
        self._write({"event": "request", **fields})

    def result(self, **fields: Any) -> None:
        self._write({"event": "result", **fields})

    def error(self, **fields: Any) -> None:
        self._write({"event": "error", **fields})

    def run_end(self, **fields: Any) -> None:
        self._write({"event": "run_end", **fields})


def read_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return records
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def discover_runs(logs_dir: str) -> list[dict[str, Any]]:
    """Summarize every run file, newest first."""
    directory = Path(logs_dir).expanduser()
    if not directory.is_dir():
        return []
    runs: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.jsonl"), key=_mtime, reverse=True):
        records = read_records(path)
        if not records:
            continue
        runs.append(summarize_run(path, records))
    return runs


def summarize_run(path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    start = _first(records, "run_start")
    end = _first(records, "run_end")
    results = [r for r in records if r.get("event") == "result"]
    errors = [r for r in records if r.get("event") == "error"]
    sources = [r.get("source") for r in results + errors if r.get("source")]
    return {
        "run_id": start.get("run_id") if start else path.stem,
        "path": str(path),
        "command": start.get("command", "unknown") if start else "unknown",
        "started": start.get("ts") if start else None,
        "finished": end.get("ts") if end else None,
        "status": (end or {}).get("status", "incomplete"),
        "results": len(results),
        "failures": len(errors),
        "sources": sources,
        "dry_run": bool(start.get("dry_run")) if start else False,
        "model": (start or {}).get("model"),
        "base_url": (start or {}).get("base_url"),
        "records": records,
    }


def load_run(logs_dir: str, run_id: str) -> dict[str, Any] | None:
    path = Path(logs_dir).expanduser() / f"{run_id}.jsonl"
    if not path.is_file():
        return None
    records = read_records(path)
    if not records:
        return None
    return summarize_run(path, records)


def results_of(run: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in run.get("records", []) if r.get("event") == "result"]


def _first(records: list[dict[str, Any]], event: str) -> dict[str, Any] | None:
    for record in records:
        if record.get("event") == event:
            return record
    return None


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def ensure_home(home: str) -> None:
    try:
        os.makedirs(os.path.join(home, "logs"), exist_ok=True)
    except OSError:
        pass


def prune(
    logs_dir: str,
    keep_days: int | None = 30,
    keep: int | None = 200,
) -> tuple[int, int, int]:
    """Delete old run logs. Returns (deleted, bytes_freed, kept)."""
    directory = Path(logs_dir).expanduser()
    if not directory.is_dir():
        return 0, 0, 0
    now = time.time()
    files = sorted(
        (path for path in directory.glob("*.jsonl") if path.is_file()),
        key=_mtime,
        reverse=True,
    )
    deleted = 0
    freed = 0
    kept = 0
    for index, path in enumerate(files):
        too_many = keep is not None and index >= keep
        stale = keep_days is not None and (now - _mtime(path)) > keep_days * 86400
        if not too_many and not stale:
            kept += 1
            continue
        try:
            size = path.stat().st_size
            path.unlink()
        except OSError:
            kept += 1
            continue
        deleted += 1
        freed += size
    return deleted, freed, kept
