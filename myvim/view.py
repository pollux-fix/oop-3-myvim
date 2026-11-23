from __future__ import annotations

from .interfaces import IRenderTarget, IRenderer
from .framework import BaseView

class EditorView(BaseView):
    """Только отрисовка; состояние скролла хранится здесь."""

    def __init__(self, target) -> None:
        self.target = target
        self._top = 0
        self._left = 0

    def render(self, model, mode_name: str, message: str) -> None:
        t = self.target
        t.clear()
        h, w = t.getmaxyx()
        if h <= 0 or w <= 0:
            return

        text_h = max(1, h - 1)

        if mode_name == "HELP":
            self._render_help(h, w)
            t.refresh()
            return

        lines = model.buffer.all_lines()

        # скролл по вертикали
        if model.row < self._top:
            self._top = model.row
        elif model.row >= self._top + text_h:
            self._top = model.row - text_h + 1
        self._top = max(0, min(self._top, max(0, len(lines) - 1)))

        # префикс номеров строк
        prefix_len = 0
        if model.show_numbers:
            prefix_len = len(f"{model.row + 1:>4} ")

        avail = max(1, w - prefix_len)
        if model.col < self._left:
            self._left = model.col
        elif model.col >= self._left + avail:
            self._left = model.col - avail + 1
        self._left = max(0, self._left)

        for sy in range(text_h):
            dr = self._top + sy
            if dr >= model.buffer.line_count():
                break

            # line = lines[dr]
            line_obj = model.get_line_obj(dr)
            x = 0
            if model.show_numbers:
                prefix = f"{dr + 1:>4} "
                t.addstr(sy, 0, prefix, t.attr_lineno())
                x = len(prefix)

            avail2 = max(0, w - x)
            if avail2 > 0:
                # Если включена подсветка (объект имеет метод get_tokens)
                if hasattr(line_obj, 'get_tokens'):
                    tokens = line_obj.get_tokens()
                    curr_x = x

                    for text_chunk, is_keyword in tokens:
                        if curr_x - x >= avail2: break
                        
                        attr = t.attr_keyword() if is_keyword else 0
                        chunk = text_chunk[:avail2 - (curr_x - x)]
                        t.addstr(sy, curr_x, chunk, attr)
                        curr_x += len(chunk)
                else:
                    # Обычная отрисовка без подсветки
                    t.addstr(sy, x, line_obj.to_py()[self._left:self._left + avail2])

        # статус-строка
        status_y = h - 1
        fname = model.filename or "[No Name]"
        mod = " [+]" if model.modified else ""
        status = (
            f" {mode_name} | {fname}{mod} | "
            f"{model.row + 1}/{len(lines)} | col {model.col + 1} "
        )
        if message:
            status = f" {message} | " + status
        t.addstr(status_y, 0, status[:max(0, w - 1)], t.attr_status())

        # курсор
        sr = model.row - self._top
        prefix_len = len(f"{model.row + 1:>4} ") if model.show_numbers else 0
        sc = prefix_len + (model.col - self._left)
        if 0 <= sr < text_h and 0 <= sc < w:
            t.move(sr, sc)

        t.refresh()

    def _render_help(self, h: int, w: int) -> None:
        lines = [
            "Help - base commands",
            ":w  save   :q quit   :q! force quit   :x save & quit",
            "i I A S r insert/replace; ESC back",
            "/ ? search; n N repeat; ESC cancel",
            "arrows; 0 ^ $ w b gg G NG",
            "x delete char; diw delete word; dd delete line",
            "yy yank line; yw yank word; p paste; u undo; U undo line",
            "Press ESC to return",
        ]
        for i, line in enumerate(lines[:max(0, h - 1)]):
            self.target.addstr(i, 0, line[:max(0, w - 1)])