from myvim.search import SearchEngine


def test_find_forward_same_line():
    lines = ["hello world"]
    assert SearchEngine().find(lines, 0, 0, "world", True) == (0, 6)


def test_find_forward_next_line():
    lines = ["aaa", "bbb", "aaa"]
    assert SearchEngine().find(lines, 0, 1, "aaa", True) == (2, 0)


def test_find_backward():
    lines = ["aaa", "bbb", "aaa"]
    # Ищем назад, начиная с 3-й строки (индекс 2, позиция 3).
    # Первое совпадение — в этой же строке в позиции 0.
    assert SearchEngine().find(lines, 2, 3, "aaa", False) == (2, 0)


def test_not_found():
    lines = ["abc"]
    assert SearchEngine().find(lines, 0, 0, "zzz", True) is None


def test_empty_query():
    assert SearchEngine().find(["abc"], 0, 0, "", True) is None


def test_empty_lines_list():
    assert SearchEngine().find([], 0, 0, "x", True) is None