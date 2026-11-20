import pytest

from myvim.commands import (
    CommandContext, CommandRegistry,
    SaveCommand, SaveAsCommand, QuitCommand, ForceQuitCommand,
    WriteQuitCommand, ReloadCommand, GotoLineCommand,
    ToggleNumbersCommand, HelpCommand, OpenCommand,
    SyntaxHighlightStub, create_default_registry,
    AbstractExCommand,
)


class FakeController:
    def __init__(self):
        self.running = True
        self.mode = "NORMAL"

    def enter_help(self):
        self.mode = "HELP"


@pytest.fixture
def ctx(model):
    return CommandContext(model, FakeController())


# ---------- конкретные команды ----------

def test_save(model, ctx, tmp_path):
    p = tmp_path / "f.txt"
    model.filename = str(p)
    model.insert_text("hello")
    SaveCommand().execute("w", ctx)
    assert p.exists()


def test_save_error_no_name(model, ctx):
    SaveCommand().execute("w", ctx)
    assert "No file name" in model.message


def test_save_as(model, ctx, tmp_path):
    p = tmp_path / "new.txt"
    model.insert_text("x")
    SaveAsCommand().execute(f"w {p}", ctx)
    assert p.exists()
    assert model.filename == str(p)


def test_quit_unmodified(model, ctx):
    QuitCommand().execute("q", ctx)
    assert ctx.controller.running is False


def test_quit_modified_blocked(model, ctx):
    model.insert_text("x")
    QuitCommand().execute("q", ctx)
    assert ctx.controller.running is True
    assert "q!" in model.message


def test_force_quit(model, ctx):
    model.insert_text("x")
    ForceQuitCommand().execute("q!", ctx)
    assert ctx.controller.running is False


def test_wq(model, ctx, tmp_path):
    p = tmp_path / "f.txt"
    model.filename = str(p)
    model.insert_text("x")
    WriteQuitCommand().execute("wq!", ctx)
    assert p.exists()
    assert ctx.controller.running is False


def test_wq_no_filename(model, ctx):
    model.insert_text("x")
    WriteQuitCommand().execute("wq!", ctx)
    assert "No file name" in model.message
    assert ctx.controller.running is True


def test_x_saves_and_quits(model, ctx, tmp_path):
    p = tmp_path / "f.txt"
    model.filename = str(p)
    model.insert_text("x")
    WriteQuitCommand().execute("x", ctx)
    assert p.exists()
    assert ctx.controller.running is False


def test_reload(model, ctx, tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"original\n")  # ИЗМЕНЕНО: пишем байты для точного контроля
    model.open_file(str(p))
    model.insert_text("CHANGED")
    ReloadCommand().execute("e!", ctx)
    assert model.buffer.get_line(0) == "original"


def test_reload_no_filename(model, ctx):
    model.insert_text("abc")
    ReloadCommand().execute("e!", ctx)
    assert model.buffer.get_line(0) == ""


def test_goto_line_cmd(model, ctx):
    model.buffer.restore(["a", "b", "c", "d"])
    GotoLineCommand().execute("3", ctx)
    assert model.row == 2


def test_toggle_numbers(model, ctx):
    ToggleNumbersCommand().execute("set num", ctx)
    assert model.show_numbers is True


def test_help(model, ctx):
    HelpCommand().execute("h", ctx)
    assert ctx.controller.mode == "HELP"


def test_open_command(model, ctx, tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"data\n")  # ИЗМЕНЕНО: пишем байты для точного контроля
    OpenCommand().execute(f"o {p}", ctx)
    assert model.buffer.get_line(0) == "data"


def test_syntax_stub(model, ctx):
    SyntaxHighlightStub().execute("sy", ctx)
    assert "not implemented" in model.message.lower() or "not implemented" in model.message


# ---------- matches() ----------

@pytest.mark.parametrize("cmd,should_match", [
    ("w", True), ("w ", False), ("w file", False),
])
def test_save_matches(cmd, should_match):
    assert SaveCommand().matches(cmd) == should_match


@pytest.mark.parametrize("cmd,should_match", [
    ("w a.txt", True), ("w  a.txt", True),
    ("w", False), ("w ", False),
])
def test_save_as_matches(cmd, should_match):
    assert SaveAsCommand().matches(cmd) == should_match


@pytest.mark.parametrize("cmd,should_match", [
    ("q", True), ("q!", False), ("wq", False),
])
def test_quit_matches(cmd, should_match):
    assert QuitCommand().matches(cmd) == should_match


@pytest.mark.parametrize("cmd,should_match", [
    ("q!", True), ("q", False),
])
def test_force_quit_matches(cmd, should_match):
    assert ForceQuitCommand().matches(cmd) == should_match


@pytest.mark.parametrize("cmd,should_match", [
    ("wq", True), ("wq!", True), ("x", True),
    ("w", False), ("q", False),
])
def test_write_quit_matches(cmd, should_match):
    assert WriteQuitCommand().matches(cmd) == should_match


@pytest.mark.parametrize("cmd,should_match", [
    ("42", True), ("0", True), ("abc", False), ("", False),
])
def test_goto_line_matches(cmd, should_match):
    assert GotoLineCommand().matches(cmd) == should_match


# ---------- реестр (OCP) ----------

def test_registry_unknown(model, ctx):
    CommandRegistry().execute("unknown", ctx)
    assert "Unknown" in model.message


def test_registry_routes_to_first_match(model, ctx):
    reg = create_default_registry()
    reg.execute("set num", ctx)
    assert model.show_numbers is True


def test_registry_ocp_extension(model, ctx):
    """OCP: добавляем команду без правки контроллера."""

    class NoOp(AbstractExCommand):
        called = False
        def matches(self, cmd): return cmd == "noop"
        def execute(self, cmd, ctx): NoOp.called = True

    reg = CommandRegistry()
    reg.register(NoOp())
    reg.execute("noop", ctx)
    assert NoOp.called is True


def test_registry_lsp_all_commands_substitutable(model, ctx, tmp_path):
    """LSP: все AbstractExCommand работают через единый интерфейс."""
    p = tmp_path / "f.txt"
    p.write_text("x\n", encoding="latin-1")
    model.filename = str(p)

    cmds = [
        SaveCommand(), SaveAsCommand(), QuitCommand(), ForceQuitCommand(),
        WriteQuitCommand(), ReloadCommand(), GotoLineCommand(),
        ToggleNumbersCommand(), HelpCommand(), OpenCommand(),
        SyntaxHighlightStub(),
    ]
    for c in cmds:
        assert isinstance(c, AbstractExCommand)


def test_default_registry_has_all_commands():
    reg = create_default_registry()
    # проверяем, что каждая из ожидаемых команд "перехватывается"
    for cmd in ["w", "w f", "q", "q!", "wq!", "x", "e!", "42",
                "set num", "h", "o f", "sy"]:
        matched = any(c.matches(cmd) for c in reg._commands)
        assert matched, f"no command matches {cmd!r}"