from __future__ import annotations

import curses

from .interfaces import IInput, IRenderTarget


class CursesAdapter(IInput, IRenderTarget):
    """Адаптер к curses. Является и IInput, и IRenderTarget — но потребители
    используют только нужный им интерфейс."""

    def __init__(self, stdscr) -> None:
        self.stdscr = stdscr
        curses.curs_set(1)
        self.stdscr.keypad(True)
        curses.noecho()
        curses.cbreak()
        self._has_colors = curses.has_colors()
        self._init_colors()

    def _init_colors(self) -> None:
        if not self._has_colors:
            return
        curses.start_color()
        try:
            curses.use_default_colors()
        except curses.error:
            pass
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_YELLOW, -1)
        curses.init_pair(3, curses.COLOR_RED, -1)

    # IInput
    def get_key(self) -> int:
        return self.stdscr.getch()

    def getmaxyx(self) -> tuple[int, int]:
        return self.stdscr.getmaxyx()

    # IRenderTarget
    def clear(self) -> None:
        self.stdscr.erase()

    def refresh(self) -> None:
        self.stdscr.refresh()

    def addstr(self, y: int, x: int, text: str, attr: int = 0) -> None:
        try:
            self.stdscr.addstr(y, x, text, attr)
        except curses.error:
            pass

    def move(self, y: int, x: int) -> None:
        try:
            self.stdscr.move(y, x)
        except curses.error:
            pass

    def attr_status(self) -> int:
        if self._has_colors:
            return curses.color_pair(1) | curses.A_BOLD
        return curses.A_REVERSE

    def attr_lineno(self) -> int:
        if self._has_colors:
            return curses.color_pair(2)
        return curses.A_DIM

    def attr_message(self) -> int:
        if self._has_colors:
            return curses.color_pair(3)
        return curses.A_BOLD