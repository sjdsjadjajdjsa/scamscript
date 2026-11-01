import os
import time
from pathlib import Path

from scamscript.store import discover_runs, prune


def make_run(directory: Path, name: str, age_days: float = 0) -> Path:
    path = directory / f"{name}.jsonl"
    path.write_text(
        '{"event": "run_start", "run_id": "%s", "command": "analyze"}\n' % name,
        encoding="utf-8",
    )
    stamp = time.time() - age_days * 86400
    os.utime(path, (stamp, stamp))
    return path


def test_prune_by_count(tmp_path):
    for index in range(5):
        make_run(tmp_path, f"run{index}")
        time.sleep(0.01)
    deleted, _, kept = prune(str(tmp_path), keep_days=None, keep=2)
    assert deleted == 3
    assert kept == 2
    assert len(discover_runs(str(tmp_path))) == 2


def test_prune_by_age(tmp_path):
    make_run(tmp_path, "old", age_days=40)
    make_run(tmp_path, "new")
    deleted, freed, kept = prune(str(tmp_path), keep_days=30, keep=None)
    assert deleted == 1
    assert kept == 1
    assert freed > 0
    assert [run["run_id"] for run in discover_runs(str(tmp_path))] == ["new"]


def test_prune_missing_dir(tmp_path):
    assert prune(str(tmp_path / "ghost")) == (0, 0, 0)
