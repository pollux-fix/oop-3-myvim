import pytest

from myvim.file_service import FileService


def test_save_and_load(tmp_path):
    p = tmp_path / "a.txt"
    svc = FileService()
    svc.save(str(p), ["one", "two"])
    assert svc.load(str(p)) == ["one", "two"]


def test_save_adds_trailing_newline(tmp_path):
    p = tmp_path / "a.txt"
    FileService().save(str(p), ["x"])
    assert p.read_bytes() == b"x\n"


def test_load_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("", encoding="latin-1")
    assert FileService().load(str(p)) == [""]


def test_load_no_trailing_newline(tmp_path):
    p = tmp_path / "nonl.txt"
    p.write_bytes(b"a\nb")
    assert FileService().load(str(p)) == ["a", "b"]


def test_latin1_roundtrip(tmp_path):
    p = tmp_path / "l1.txt"
    svc = FileService()
    lines = ["café", "naïve"]
    svc.save(str(p), lines)
    assert svc.load(str(p)) == lines


def test_encoding_is_latin1(tmp_path):
    p = tmp_path / "l1.txt"
    svc = FileService()
    svc.save(str(p), ["café"])
    raw = p.read_bytes()
    assert b"caf\xe9" in raw  # именно 1 байт на символ


def test_nonexistent_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        FileService().load(str(tmp_path / "nope.txt"))