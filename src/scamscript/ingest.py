"""Script file ingestion and directory collection."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

TEXT_SUFFIXES = frozenset(
    {".txt", ".md", ".markdown", ".transcript", ".srt", ".vtt", ".log", ".json", ".text"}
)
MAX_CHARS = 400_000


class IngestError(Exception):
    """Raised when a path cannot be turned into a script."""


@dataclass(slots=True)
class ScriptFile:
    path: Path
    text: str
    truncated: bool = False

    @property
    def name(self) -> str:
        return self.path.name


def read_script(path: Path) -> ScriptFile:
    path = Path(path).expanduser().resolve()
    if not path.exists():
        raise IngestError(f"no such file: {path}")
    if not path.is_file():
        raise IngestError(f"not a file: {path}")
    if path.suffix.lower() not in TEXT_SUFFIXES:
        raise IngestError(
            f"unsupported file type {path.suffix or '(none)'} for {path}; "
            f"expected one of {', '.join(sorted(TEXT_SUFFIXES))}"
        )
    before = _stamp(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise IngestError(f"cannot read {path}: {exc}") from exc
    if _stamp(path) != before:
        raise IngestError(f"file changed while reading: {path}")
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n")
    truncated = len(text) > MAX_CHARS
    if truncated:
        text = text[:MAX_CHARS]
    if not text.strip():
        raise IngestError(f"file is empty: {path}")
    return ScriptFile(path=path.resolve(), text=text, truncated=truncated)


def _stamp(path: Path) -> tuple[int, int] | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return (stat.st_size, stat.st_mtime_ns)


def collect_scripts(directory: Path, recursive: bool = False) -> list[ScriptFile]:
    directory = Path(directory).expanduser().resolve()
    if not directory.exists():
        raise IngestError(f"no such directory: {directory}")
    if not directory.is_dir():
        raise IngestError(f"not a directory: {directory}")

    paths: list[Path] = []
    seen: set[Path] = set()
    for root, dirs, files in os.walk(directory, followlinks=True):
        real = Path(root).resolve()
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        if not recursive:
            dirs[:] = []
        else:
            dirs[:] = [name for name in dirs if not name.startswith(".")]
        for name in files:
            candidate = Path(root) / name
            if name.startswith(".") or candidate.suffix.lower() not in TEXT_SUFFIXES:
                continue
            if candidate.is_file():
                paths.append(candidate)
    paths.sort(key=lambda item: str(item).lower())
    if not paths:
        raise IngestError(
            f"no script files found in {directory} "
            f"(expected extensions: {', '.join(sorted(TEXT_SUFFIXES))})"
        )

    scripts: list[ScriptFile] = []
    for candidate in paths:
        try:
            scripts.append(read_script(candidate))
        except IngestError:
            continue
    if not scripts:
        raise IngestError(f"no readable script files in {directory}")
    return scripts
