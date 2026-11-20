from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from .history import CommandHistory


class CommandContext:
    """Всё, что нужно команде: модель + управление контроллером."""

    def __init__(self, model, controller) -> None:
        self.model = model
        self.controller = controller

    def quit(self) -> None:
        self.controller.running = False

    def enter_help(self) -> None:
        self.controller.enter_help()


class AbstractExCommand(ABC):
    """Базовый класс для всех :команд (LSP — любую можно подставить в реестр)."""

    @abstractmethod
    def matches(self, cmd: str) -> bool: ...

    @abstractmethod
    def execute(self, cmd: str, ctx: CommandContext) -> None: ...


class ToggleNumbersCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "set num"
    
    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.model.number_lines()

class SyntaxHighlightCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "sy"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.model.toggle_syntax_highlight()

class HistoryCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "history"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        hist = CommandHistory().get_last(5)
        if not hist:
            ctx.model.message = "History is empty"
        else:
            ctx.model.message = "History: " + " | ".join(hist)


#   конкретные команды  

class SaveCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "w"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        try:
            ctx.model.save_file()
        except Exception as exc:
            ctx.model.message = str(exc)


class SaveAsCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd.startswith("w ") and len(cmd) > 2

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        try:
            ctx.model.save_file(cmd[2:].strip())
        except Exception as exc:
            ctx.model.message = str(exc)


class QuitCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "q"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        if ctx.model.modified:
            ctx.model.message = "No write since last change (use q!)"
        else:
            ctx.quit()


class ForceQuitCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "q!"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.quit()


class WriteQuitCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd in ("wq", "wq!", "x")

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        if not ctx.model.filename:
            ctx.model.message = "No file name"
            return
        try:
            ctx.model.save_file()
            ctx.quit()
        except Exception as exc:
            ctx.model.message = str(exc)


class ReloadCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "e!"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        try:
            if ctx.model.filename:
                ctx.model.open_file(ctx.model.filename)
            else:
                ctx.model.clear_all()
                ctx.model.message = "Reverted"
        except Exception as exc:
            ctx.model.message = str(exc)


class GotoLineCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd.isdigit() and len(cmd) > 0

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.model.goto_line(int(cmd))


class ToggleNumbersCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "set num"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.model.toggle_numbers()


class HelpCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "h"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.enter_help()


class OpenCommand(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd.startswith("o ") and len(cmd) > 2

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        try:
            ctx.model.open_file(cmd[2:].strip())
        except Exception as exc:
            ctx.model.message = str(exc)


class SyntaxHighlightStub(AbstractExCommand):
    def matches(self, cmd: str) -> bool:
        return cmd == "sy"

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        ctx.model.message = "Syntax highlighting is not implemented in base version"


#   реестр (OCP)  

class CommandRegistry:
    """Регистр :команд. Новая команда = register(...) — контроллер не правится."""

    def __init__(self) -> None:
        self._commands: list[AbstractExCommand] = []

    def register(self, command: AbstractExCommand) -> None:
        self._commands.append(command)

    def execute(self, cmd: str, ctx: CommandContext) -> None:
        for c in self._commands:
            if c.matches(cmd):
                c.execute(cmd, ctx)
                return
        ctx.model.message = f"Unknown command: {cmd}"


def create_default_registry() -> CommandRegistry:
    reg = CommandRegistry()
    # порядок важен: специфичные паттерны раньше общих
    reg.register(ForceQuitCommand())
    reg.register(WriteQuitCommand())
    reg.register(SaveAsCommand())
    reg.register(OpenCommand())

    reg.register(ToggleNumbersCommand())
    reg.register(SyntaxHighlightCommand())
    reg.register(HistoryCommand())

    reg.register(SaveCommand())
    reg.register(QuitCommand())
    reg.register(ReloadCommand())
    reg.register(GotoLineCommand())
    reg.register(HelpCommand())

    reg.register(SyntaxHighlightStub())
    return reg