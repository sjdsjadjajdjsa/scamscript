import pytest

from scamscript.ingest import IngestError, collect_scripts, read_script


def write(path, text="CALLER: hello\n"):
    path.write_text(text, encoding="utf-8")
    return path


def test_reads_text_file(tmp_path):
    script = write(tmp_path / "a.txt")
    result = read_script(script)
    assert result.text.startswith("CALLER")
    assert result.path.is_absolute()


def test_normalises_crlf(tmp_path):
    script = tmp_path / "a.txt"
    script.write_bytes(b"one\r\ntwo\r\n")
    assert read_script(script).text == "one\ntwo\n"


def test_truncates_huge_file(tmp_path, monkeypatch):
    import scamscript.ingest as ingest

    monkeypatch.setattr(ingest, "MAX_CHARS", 5)
    script = write(tmp_path / "a.txt", "abcdefgh")
    result = read_script(script)
    assert result.text == "abcde"
    assert result.truncated


def test_unknown_suffix(tmp_path):
    script = write(tmp_path / "a.pdf")
    with pytest.raises(IngestError, match="unsupported"):
        read_script(script)


def test_empty_file(tmp_path):
    script = write(tmp_path / "a.txt", "  \n")
    with pytest.raises(IngestError, match="empty"):
        read_script(script)


def test_missing_file(tmp_path):
    with pytest.raises(IngestError, match="no such file"):
        read_script(tmp_path / "nope.txt")


def test_directory_arg(tmp_path):
    with pytest.raises(IngestError, match="not a file"):
        read_script(tmp_path)


def test_collect_sorted_and_filtered(tmp_path):
    write(tmp_path / "b.txt")
    write(tmp_path / "a.md")
    write(tmp_path / "skip.pdf")
    write(tmp_path / ".hidden.txt")
    names = [item.name for item in collect_scripts(tmp_path)]
    assert names == ["a.md", "b.txt"]


def test_collect_recursive(tmp_path):
    nested = tmp_path / "nested"
    nested.mkdir()
    write(nested / "deep.txt")
    assert [item.name for item in collect_scripts(tmp_path, recursive=True)] == ["deep.txt"]
    with pytest.raises(IngestError, match="no script files"):
        collect_scripts(tmp_path)


def test_collect_empty_dir(tmp_path):
    with pytest.raises(IngestError, match="no script files"):
        collect_scripts(tmp_path)


def test_collect_missing_dir(tmp_path):
    with pytest.raises(IngestError, match="no such directory"):
        collect_scripts(tmp_path / "ghost")


def test_collect_skips_unreadable(tmp_path):
    write(tmp_path / "ok.txt")
    (tmp_path / "empty.txt").write_text("", encoding="utf-8")
    assert [item.name for item in collect_scripts(tmp_path)] == ["ok.txt"]
