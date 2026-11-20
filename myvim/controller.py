from __future__ import annotations

import curses
from enum import Enum

from .commands import CommandContext, CommandRegistry
from .interfaces import IInput, IRenderer


class Mode(Enum):
    NORMAL = "NORMAL"
    COMMAND = "COMMAND"
    INSERT = "INSERT"
    SEARCH = "SEARCH"
    HELP = "HELP"


class EditorController:
    def __init__(
        self,
        model,
        view: IRenderer,
        input_source: IInput,
        registry: CommandRegistry,
    ) -> None:
        self.model = model
        self.view = view
        self.input = input_source
        self.registry = registry
        self.ctx = CommandContext(model, self)

        self.mode = Mode.NORMAL
        self.running = True
        self.pending = ""
        self.command_buffer = ""
        self.search_buffer = ""
        self.search_forward = True
        self.replace_once = False

    def enter_help(self) -> None:
        self.mode = Mode.HELP

    #   главный цикл  

    def run(self) -> None:
        while self.running:
            msg = self.model.message
            if self.mode is Mode.COMMAND:
                msg = ":" + self.command_buffer
            elif self.mode is Mode.SEARCH:
                msg = ("/" if self.search_forward else "?") + self.search_buffer

            self.view.render(self.model, self.mode.value, msg)

            key = self.input.get_key()
            if key == -1:
                break

            # Очищаем сообщение только когда знаем, что цикл продолжится
            self.model.message = ""

            if self.mode is Mode.NORMAL:
                self._handle_normal(key)
            elif self.mode is Mode.INSERT:
                self._handle_insert(key)
            elif self.mode is Mode.COMMAND:
                self._handle_command(key)
            elif self.mode is Mode.SEARCH:
                self._handle_search(key)
            elif self.mode is Mode.HELP:
                if key == 27:
                    self.mode = Mode.NORMAL

    #   NORMAL  

    def _handle_normal(self, key: int) -> None:
        if key == 27:
            self.pending = ""
            self.replace_once = False
            return

        if self.replace_once:
            ch = self._key_to_char(key)
            if ch and 32 <= ord(ch) <= 255:
                self.model.begin_line_edit()
                self.model.replace_char(ch)
                self.replace_once = False
            return

        if key == curses.KEY_LEFT:  self.model.move_left();  self.pending = ""; return
        if key == curses.KEY_RIGHT: self.model.move_right(); self.pending = ""; return
        if key == curses.KEY_UP:    self.model.move_up();    self.pending = ""; return
        if key == curses.KEY_DOWN:  self.model.move_down();  self.pending = ""; return
        if key == curses.KEY_PPAGE:
            h, _ = self.input.getmaxyx()
            self.model.page_up(max(1, h - 2)); self.pending = ""; return
        if key == curses.KEY_NPAGE:
            h, _ = self.input.getmaxyx()
            self.model.page_down(max(1, h - 2)); self.pending = ""; return

        ch = self._key_to_char(key)
        if not ch:
            return

        # многосимвольные
        if self.pending == "g":
            if ch == "g":
                self.model.goto_top()
            self.pending = ""
            return
        if self.pending == "d":
            if ch == "d":
                self.model.begin_line_edit(); self.model.delete_line()
                self.pending = ""; return
            if ch == "i":
                self.pending = "di"; return
            self.pending = ""; return
        if self.pending == "di":
            if ch == "w":
                self.model.begin_line_edit(); self.model.delete_word_under_cursor()
                self.pending = ""; return
            self.pending = ""; return
        if self.pending == "y":
            if ch == "y":
                self.model.yank_line(); self.pending = ""; return
            if ch == "w":
                self.model.yank_word(); self.pending = ""; return
            self.pending = ""; return
        if self.pending.isdigit():
            if ch == "G":
                self.model.goto_line(int(self.pending)); self.pending = ""; return
            if ch.isdigit():
                self.pending += ch; return
            self.pending = ""; return

        # одиночные
        if ch.isdigit():
            if ch == "0":
                self.model.move_home()
            else:
                self.pending = ch
            return
        if ch == "g": self.pending = "g"; return
        if ch == "d": self.pending = "d"; return
        if ch == "y": self.pending = "y"; return

        if ch == "G": self.model.goto_bottom();  return
        if ch == "^": self.model.move_home();    return
        if ch == "$": self.model.move_end();     return
        if ch == "w": self.model.move_word_forward();  return
        if ch == "b": self.model.move_word_backward(); return

        if ch == "x":
            self.model.begin_line_edit(); self.model.delete_char(); return
        if ch == "p":
            self.model.begin_line_edit(); self.model.paste_after(); return
        if ch == "u": self.model.undo();      return
        if ch == "U": self.model.undo_line(); return

        if ch == "i": self._begin_insert("i"); return
        if ch == "a": self._begin_insert("a"); return
        if ch == "I": self._begin_insert("I"); return
        if ch == "A": self._begin_insert("A"); return
        if ch == "S": self._begin_insert("S"); return
        if ch == "r":
            self.replace_once = True
            self.model.message = "replace: press char"
            return

        if ch == "/":
            self.mode = Mode.SEARCH; self.search_forward = True
            self.search_buffer = ""; return
        if ch == "?":
            self.mode = Mode.SEARCH; self.search_forward = False
            self.search_buffer = ""; return
        if ch == "n": self.model.repeat_search(False); return
        if ch == "N": self.model.repeat_search(True);  return
        if ch == ":":
            self.mode = Mode.COMMAND
            self.command_buffer = ""
            return

    def _begin_insert(self, kind: str) -> None:
        self.model.begin_line_edit()
        if kind == "a":
            self.model.move_right()          # ← курсор на символ вправо
        elif kind == "I":
            self.model.move_home()
        elif kind == "A":
            self.model.move_end()
        elif kind == "S":
            self.model.clear_current_line()
        self.mode = Mode.INSERT
        self.pending = ""

    #   INSERT  

    def _handle_insert(self, key: int) -> None:
        if key == 27:
            self.mode = Mode.NORMAL
            return
        if key == curses.KEY_LEFT:  self.model.move_left();  return
        if key == curses.KEY_RIGHT: self.model.move_right(); return
        if key == curses.KEY_UP:    self.model.move_up();    return
        if key == curses.KEY_DOWN:  self.model.move_down();  return
        if key in (10, 13):
            self.model.newline(); return
        if key in (8, 127, curses.KEY_BACKSPACE):
            self.model.backspace(); return
        ch = self._key_to_char(key)
        if ch and 32 <= ord(ch) <= 255:
            self.model.insert_char(ch)

    #   COMMAND  

    def _handle_command(self, key: int) -> None:
        if key == 27:
            self.mode = Mode.NORMAL
            self.command_buffer = ""
            return
        if key in (10, 13):
            cmd = self.command_buffer.strip()
            self.command_buffer = ""
            self.mode = Mode.NORMAL
            if cmd:
                self.registry.execute(cmd, self.ctx)
            return
        if key in (8, 127, curses.KEY_BACKSPACE):
            self.command_buffer = self.command_buffer[:-1]
            return
        ch = self._key_to_char(key)
        if ch and 32 <= ord(ch) <= 255:
            self.command_buffer += ch

    #   SEARCH  

    def _handle_search(self, key: int) -> None:
        if key == 27:
            self.mode = Mode.NORMAL
            self.search_buffer = ""
            return
        if key in (10, 13):
            query = self.search_buffer
            self.mode = Mode.NORMAL
            if query:
                if self.model.search(query, self.search_forward):
                    self.model.message = f"Found: {query}"
            return
        if key in (8, 127, curses.KEY_BACKSPACE):
            self.search_buffer = self.search_buffer[:-1]
            return
        ch = self._key_to_char(key)
        if ch and 32 <= ord(ch) <= 255:
            self.search_buffer += ch

    @staticmethod
    def _key_to_char(key: int) -> str:
        return chr(key) if 0 <= key <= 255 else ""