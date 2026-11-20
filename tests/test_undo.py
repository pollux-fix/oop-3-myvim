from myvim.undo import UndoManager


def test_empty():
    u = UndoManager()
    assert u.is_empty()
    assert u.pop() is None


def test_push_pop():
    u = UndoManager()
    u.push("a")
    u.push("b")
    assert not u.is_empty()
    assert u.pop() == "b"
    assert u.pop() == "a"
    assert u.is_empty()


def test_max_size_trim():
    u = UndoManager(max_size=3)
    for i in range(5):
        u.push(i)
    # остались только 2, 3, 4
    assert u.pop() == 4
    assert u.pop() == 3
    assert u.pop() == 2
    assert u.pop() is None


def test_clear():
    u = UndoManager()
    u.push("a")
    u.clear()
    assert u.is_empty()