from myvim.buffer import TextBuffer
from myvim.commands import (
    CommandContext, CommandRegistry, SaveCommand, QuitCommand,
    create_default_registry,
)
from myvim.file_service import FileService
from myvim.model import EditorModel
from myvim.search import SearchEngine
from myvim.undo import UndoManager


def _make_model():
    return EditorModel(
        buffer=TextBuffer(),
        file_service=FileService(),
        undo=UndoManager(),
        search=SearchEngine(),
    )


def test_initial_state():
    m = _make_model()
    assert m.buffer.line_count() == 1
    assert m.buffer.get_line(0) == ""
    assert (m.row, m.col) == (0, 0)


def test_insert_newline_backspace():
    m = _make_model()
    m.insert_text("ab")
    m.newline()
    m.insert_text("c")
    assert m.buffer.all_lines() == ["ab", "c"]
    assert (m.row, m.col) == (1, 1)
    
    # Ставим курсор в начало второй строки (перед буквой 'c')
    m.col = 0
    # Теперь backspace должен склеить строки: "ab" + "c" = "abc"
    m.backspace()
    assert m.buffer.all_lines() == ["abc"]


def test_word_navigation():
    m = _make_model()
    m.insert_text("hello world")
    m.col = 0
    m.move_word_forward()
    assert m.col == 4
    m.move_word_forward()
    assert m.col == 10
    m.move_word_backward()
    assert m.col == 6
    m.move_word_backward()
    assert m.col == 0


def test_undo_and_undo_line():
    m = _make_model()
    m.insert_text("abc")
    m.undo()
    assert m.buffer.get_line(0) == ""
    m.begin_line_edit()
    m.insert_text("xyz")
    m.undo_line()
    assert m.buffer.get_line(0) == ""


def test_yank_paste_line():
    m = _make_model()
    m.insert_text("one")
    m.newline()
    m.insert_text("two")
    m.row = 0
    m.yank_line()
    m.paste_after()
    assert m.buffer.all_lines() == ["one", "one", "two"]


def test_search_forward_repeat():
    m = _make_model()
    m.buffer.restore(["alpha", "beta", "gamma", "beta"])
    m.row = m.col = 0
    assert m.search("beta", forward=True) is True
    assert (m.row, m.col) == (1, 0)
    assert m.repeat_search() is True
    assert m.row == 3


def test_save_open(tmp_path):
    p = tmp_path / "sample.txt"
    m = _make_model()
    m.insert_text("hello")
    m.save_file(str(p))
    assert p.read_text(encoding="latin-1") == "hello\n"
    m2 = _make_model()
    m2.open_file(str(p))
    assert m2.buffer.get_line(0) == "hello"
    assert m2.modified is False


def test_command_registry_ocp():
    """OCP-демонстрация: добавляем новую команду без правки контроллера."""
    reg = CommandRegistry()

    from myvim.commands import AbstractExCommand

    class DummyCommand(AbstractExCommand):
        def __init__(self):
            self.called = False

        def matches(self, cmd):
            return cmd == "dummy"

        def execute(self, cmd, ctx):
            self.called = True
            ctx.model.message = "dummy called"

    dummy = DummyCommand()
    reg.register(dummy)

    m = _make_model()
    ctx = CommandContext(m, controller=None)
    reg.execute("dummy", ctx)
    assert dummy.called is True
    assert m.message == "dummy called"


def test_default_registry_routes_commands():
    reg = create_default_registry()
    m = _make_model()
    ctx = CommandContext(m, controller=None)

    reg.execute("set num", ctx)
    assert m.show_numbers is True
    reg.execute("set num", ctx)
    assert m.show_numbers is False

    reg.execute("42", ctx)
    assert m.row == 0  # файл пуст — одна строка


def test_command_lsp_substitutable():
    """LSP: любая AbstractExCommand подставляется в реестр."""
    from myvim.commands import AbstractExCommand

    class NoOp(AbstractExCommand):
        def matches(self, cmd):
            return cmd == "noop"

        def execute(self, cmd, ctx):
            pass

    reg = CommandRegistry()
    reg.register(SaveCommand())
    reg.register(QuitCommand())
    reg.register(NoOp())

    m = _make_model()
    ctx = CommandContext(m, controller=None)
    reg.execute("noop", ctx)          # NoOp
    reg.execute("unknown_cmd", ctx)   # -> Unknown command
    assert "Unknown" in m.message