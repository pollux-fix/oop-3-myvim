from myvim.buffer import TextBuffer


def test_initial_single_empty_line():
    b = TextBuffer()
    assert b.line_count() == 1
    assert b.get_line(0) == ""


def test_initial_with_lines():
    b = TextBuffer(["a", "b"])
    assert b.line_count() == 2
    assert b.all_lines() == ["a", "b"]


def test_set_line():
    b = TextBuffer(["a"])
    b.set_line(0, "abc")
    assert b.get_line(0) == "abc"


def test_insert_line():
    b = TextBuffer(["a", "c"])
    b.insert_line(1, "b")
    assert b.all_lines() == ["a", "b", "c"]


def test_delete_line_keeps_non_empty():
    b = TextBuffer(["only"])
    b.delete_line(0)
    assert b.line_count() == 1
    assert b.get_line(0) == ""


def test_insert_text():
    b = TextBuffer(["abc"])
    b.insert_text(0, 1, "XY")
    assert b.get_line(0) == "aXYbc"


def test_delete_range():
    b = TextBuffer(["abcdef"])
    removed = b.delete_range(0, 2, 4)
    assert removed == "cd"
    assert b.get_line(0) == "abef"


def test_replace_range():
    b = TextBuffer(["abcdef"])
    b.replace_range(0, 2, 4, "XY")
    assert b.get_line(0) == "abXYef"


def test_all_lines_and_restore():
    b = TextBuffer(["x", "y"])
    snap = b.all_lines()
    b.restore(["p", "q", "r"])
    assert b.all_lines() == ["p", "q", "r"]
    b.restore(snap)
    assert b.all_lines() == ["x", "y"]