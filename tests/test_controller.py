import curses

import pytest

from myvim.commands import create_default_registry
from myvim.controller import EditorController, Mode
from myvim.file_service import FileService
from myvim.model import EditorModel
from myvim.search import SearchEngine
from myvim.undo import UndoManager
from myvim.buffer import TextBuffer


class FakeInput:
    def __init__(self, keys):
        self._keys = list(keys)
        self._pos = 0

    def get_key(self):
        if self._pos >= len(self._keys):
            return -1
        k = self._keys[self._pos]
        self._pos += 1
        return k

    def getmaxyx(self):
        return (24, 80)


class FakeRenderTarget:
    """Ничего не рисует, только запоминает вызовы для проверки."""
    def __init__(self):
        self.calls = []
        self.moved_to = None

    def clear(self): pass
    def refresh(self): pass
    def getmaxyx(self): return (24, 80)
    def addstr(self, y, x, text, attr=0):
        self.calls.append((y, x, text))
    def move(self, y, x):
        self.moved_to = (y, x)
    def attr_status(self): return 0
    def attr_lineno(self): return 0
    def attr_message(self): return 0


class FakeView:
    """Заглушка View — не нужен реальный curses."""
    def __init__(self):
        self.target = FakeRenderTarget()
        self.last_mode = None
        self.last_message = None

    def render(self, model, mode_name, message):
        self.last_mode = mode_name
        self.last_message = message
        # имитируем view — выставляем курсор
        self.target.move(model.row, model.col)


def _build(keys, initial_lines=None):
    buf = TextBuffer(initial_lines) if initial_lines else TextBuffer()
    model = EditorModel(
        buffer=buf,
        file_service=FileService(),
        undo=UndoManager(),
        search=SearchEngine(),
    )
    view = FakeView()
    inp = FakeInput(keys)
    ctrl = EditorController(
        model=model, view=view, input_source=inp,
        registry=create_default_registry(),
    )
    return ctrl, model, view


# ---------- базовые ----------

def test_starts_in_normal_mode():
    ctrl, _, _ = _build([])
    assert ctrl.mode is Mode.NORMAL


def test_escape_stays_in_normal():
    ctrl, _, _ = _build([27, -1])  # ESC
    ctrl.run()
    assert ctrl.mode is Mode.NORMAL


# ---------- режим COMMAND ----------

def test_enter_command_mode():
    ctrl, _, _ = _build([ord(":"), 27])   # : затем ESC
    ctrl.run()
    assert ctrl.mode is Mode.NORMAL  # ESC вышел


def test_escape_from_command():
    ctrl, _, _ = _build([ord(":"), 27])
    ctrl.run()
    assert ctrl.mode is Mode.NORMAL


def test_command_set_num():
    ctrl, model, _ = _build(list(map(ord, ":set num\n")) + [27])
    ctrl.run()
    assert model.show_numbers is True


def test_command_goto_line():
    ctrl, model, _ = _build(
        list(map(ord, ":2\n")) + [27],
        initial_lines=["a", "b", "c"],
    )
    ctrl.run()
    assert model.row == 1


def test_command_writes_file(tmp_path):
    p = tmp_path / "f.txt"
    keys = list(map(ord, f":w {p}\n")) + [27]
    ctrl, model, _ = _build(keys)
    model.insert_text("hi")
    ctrl.run()
    assert p.exists()


def test_unknown_command_message():
    ctrl, model, _ = _build(list(map(ord, ":blah\n")))
    ctrl.run()
    assert "Unknown" in model.message


def test_command_quit_no_modifications():
    ctrl, _, _ = _build(list(map(ord, ":q\n")))
    ctrl.run()
    assert ctrl.running is False


def test_command_quit_blocked_when_modified():
    ctrl, model, _ = _build(list(map(ord, ":q\n")))
    model.insert_text("x")
    ctrl.run()
    assert ctrl.running is True
    assert "q!" in model.message


def test_command_force_quit():
    ctrl, model, _ = _build(list(map(ord, ":q!\n")))
    model.insert_text("x")
    ctrl.run()
    assert ctrl.running is False


# ---------- режим INSERT ----------

def test_enter_insert_via_keys():
    for key in ["i", "I", "A", "S", "a", "r"]:
        ctrl, _, _ = _build([ord(key), 27, -1])
        ctrl.run()
        # после ESC — обратно в NORMAL
        assert ctrl.mode is Mode.NORMAL


def test_i_inserts_before_cursor():
    keys = list(map(ord, "iAB")) + [27, -1]
    ctrl, model, _ = _build(keys)
    model.buffer.restore(["XY"])
    model.col = 1
    ctrl.run()
    assert model.buffer.get_line(0) == "XABY"


def test_a_moves_right_then_inserts():
    keys = [ord("a")] + list(map(ord, "ZZ")) + [27, -1]
    ctrl, model, _ = _build(keys)
    model.buffer.restore(["XY"])
    model.col = 0
    ctrl.run()
    # a сдвинул на 1, вставка "ZZ" дала "XZZY"
    assert model.buffer.get_line(0) == "XZZY"


def test_I_moves_home():
    keys = [ord("I")] + list(map(ord, "AB")) + [27, -1]
    ctrl, model, _ = _build(keys)
    model.buffer.restore(["xyz"])
    model.col = 2
    ctrl.run()
    assert model.buffer.get_line(0) == "ABxyz"


def test_A_moves_end():
    keys = [ord("A")] + list(map(ord, "AB")) + [27, -1]
    ctrl, model, _ = _build(keys)
    model.buffer.restore(["xyz"])
    ctrl.run()
    assert model.buffer.get_line(0) == "xyzAB"


def test_S_clears_line():
    keys = [ord("S")] + list(map(ord, "AB")) + [27, -1]
    ctrl, model, _ = _build(keys)
    model.buffer.restore(["old stuff"])
    ctrl.run()
    assert model.buffer.get_line(0) == "AB"


def test_r_replace():
    keys = [ord("r"), ord("Z"), -1]
    ctrl, model, _ = _build(keys)
    model.buffer.restore(["abc"])
    model.col = 1
    ctrl.run()
    assert model.buffer.get_line(0) == "aZc"


def test_escape_from_insert():
    ctrl, _, _ = _build([ord("i"), 27, -1])
    ctrl.run()
    assert ctrl.mode is Mode.NORMAL


# ---------- режим SEARCH ----------

def test_enter_search_modes():
    ctrl, _, _ = _build([ord("/"), 27, ord("?"), 27])
    ctrl.run()
    assert ctrl.mode is Mode.NORMAL


def test_search_forward_end_to_end():
    keys = list(map(ord, "/beta\n")) + [-1]
    ctrl, model, _ = _build(keys, initial_lines=["alpha", "beta", "gamma"])
    model.row = model.col = 0
    ctrl.run()
    assert model.row == 1


def test_search_backward_end_to_end():
    keys = list(map(ord, "?alpha\n")) + [-1]
    ctrl, model, _ = _build(keys, initial_lines=["alpha", "beta", "gamma"])
    model.row = 2
    ctrl.run()
    assert model.row == 0


def test_escape_from_search():
    ctrl, _, _ = _build([ord("/"), 27, -1])
    ctrl.run()
    assert ctrl.mode is Mode.NORMAL


def test_search_not_found():
    keys = list(map(ord, "/zzz\n")) + [-1]
    ctrl, model, _ = _build(keys, initial_lines=["a"])
    ctrl.run()
    assert "not found" in model.message


# ---------- HELP ----------

def test_help_command_switches_mode():
    keys = list(map(ord, ":h\n")) + [27]
    ctrl, _, _ = _build(keys)
    # прогоняем цикл
    ctrl.run()
    # ESC вернул в NORMAL
    assert ctrl.mode is Mode.NORMAL


# ---------- View / статус-строка ----------

def test_status_bar_contains_fields():
    """Рендер вызывается с корректным mode name и сообщением."""
    ctrl, model, view = _build(list(map(ord, ":set num\n")) + [27, -1])
    ctrl.run()
    # после ESC мы уже в NORMAL
    # проверим, что хотя бы раз render получил mode NORMAL
    assert view.last_mode == "NORMAL"


def test_cursor_position():
    """FakeView двигает курсор согласно модели."""
    ctrl, model, view = _build([curses.KEY_RIGHT, curses.KEY_RIGHT, -1],
                               initial_lines=["abc"])
    ctrl.run()
    assert view.target.moved_to == (0, 2)


# ---------- Верификация MVC-связки ----------

def test_mvc_wiring():
    ctrl, model, view = _build([])
    # три слоя сосуществуют и связаны
    assert ctrl.model is model
    assert ctrl.view is view
    assert hasattr(view, "render")
    assert hasattr(model, "buffer")
    assert hasattr(ctrl, "input")
    assert hasattr(ctrl, "registry")