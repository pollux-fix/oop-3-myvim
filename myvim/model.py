from __future__ import annotations

from typing import Any, List, Optional, Tuple

from .buffer import TextBuffer
from .file_service import FileService
from .interfaces import IFileService, ISearchService, ITextBuffer, IUndoService
from .mystring import MyString, SyntaxHighlightDecorator
from .search import SearchEngine
from .undo import UndoManager
from .yank import YankBuffer


def _is_word_char(ch: str) -> bool:
    return ch.isalnum() or ch == "_"


class EditorModel:
    """Фасад: единый API редактирования для контроллера."""

    def __init__(
        self,
        buffer: ITextBuffer | None = None,
        file_service: IFileService | None = None,
        undo: IUndoService | None = None,
        search: ISearchService | None = None,
    ) -> None:
        # DIP: зависимости приходят извне (или дефолты)
        self.buffer: ITextBuffer = buffer or TextBuffer()
        self.file_service: IFileService = file_service or FileService()
        # переименовано в undo_manager, чтобы не конфликтовать с методом undo()
        self.undo_manager: IUndoService = undo or UndoManager() 
        self.search_service: ISearchService = search or SearchEngine()
        self.yank = YankBuffer()

        # Состояние сессии
        self.row = 0
        self.col = 0
        self.filename: Optional[str] = None
        self.modified = False
        self.show_numbers = False
        self.highlight_syntax = False

        self.last_search = ""
        self.last_search_forward = True
        self.message = ""

        self._line_before_edit: Optional[Tuple[int, str]] = None

    #   курсор  

    def clamp(self) -> None:
        n = self.buffer.line_count()
        self.row = max(0, min(self.row, n - 1))
        self.col = max(0, min(self.col, len(self.buffer.get_line(self.row))))

    #   undo  

    def _snapshot(self) -> Tuple[List[str], int, int, bool]:
        return (self.buffer.all_lines(), self.row, self.col, self.modified)

    def _push_undo(self) -> None:
        self.undo_manager.push(self._snapshot()) # ИЗМЕНЕНО

    def begin_line_edit(self) -> None:
        self._line_before_edit = (self.row, self.buffer.get_line(self.row))

    def undo(self) -> None:
        snap = self.undo_manager.pop() # ИЗМЕНЕНО
        if snap is None:
            self.message = "Nothing to undo"
            return
        lines, row, col, modified = snap
        self.buffer.restore(lines)
        self.row, self.col, self.modified = row, col, modified
        self.clamp()
        self.message = "Undo"

    def undo_line(self) -> None:
        if self._line_before_edit is None:
            self.message = "Nothing to undo in line"
            return
        row, old = self._line_before_edit
        if 0 <= row < self.buffer.line_count():
            self.buffer.set_line(row, old)
            self.modified = True
            self.clamp()
            self.message = "Line restored"
        self._line_before_edit = None

    #   редактирование  

    def insert_text(self, text: str) -> None:
        if not text:
            return
        self._push_undo()
        self.buffer.insert_text(self.row, self.col, text)
        self.col += len(text)
        self.modified = True

    def insert_char(self, ch: str) -> None:
        if len(ch) != 1:
            raise ValueError("single character expected")
        self.insert_text(ch)

    def newline(self) -> None:
        self._push_undo()
        line = self.buffer.get_line(self.row)
        left, right = line[: self.col], line[self.col:]
        self.buffer.set_line(self.row, left)
        self.buffer.insert_line(self.row + 1, right)
        self.row += 1
        self.col = 0
        self.modified = True

    def backspace(self) -> None:
        line = self.buffer.get_line(self.row)
        if self.col > 0:
            self._push_undo()
            self.buffer.delete_range(self.row, self.col - 1, self.col)
            self.col -= 1
            self.modified = True
        elif self.row > 0:
            self._push_undo()
            prev = self.buffer.get_line(self.row - 1)
            cur = self.buffer.get_line(self.row)
            self.buffer.set_line(self.row - 1, prev + cur)
            self.buffer.delete_line(self.row)
            self.row -= 1
            self.col = len(prev)
            self.modified = True

    def delete_char(self) -> None:
        line = self.buffer.get_line(self.row)
        if self.col < len(line):
            self._push_undo()
            self.buffer.delete_range(self.row, self.col, self.col + 1)
            self.modified = True
        elif self.row + 1 < self.buffer.line_count():
            self._push_undo()
            nxt = self.buffer.get_line(self.row + 1)
            self.buffer.set_line(self.row, line + nxt)
            self.buffer.delete_line(self.row + 1)
            self.modified = True

    def clear_current_line(self) -> None:
        self._push_undo()
        self.buffer.set_line(self.row, "")
        self.col = 0
        self.modified = True

    def replace_char(self, ch: str) -> None:
        if len(ch) != 1:
            raise ValueError("single character expected")
        self._push_undo()
        line = self.buffer.get_line(self.row)
        if self.col < len(line):
            self.buffer.replace_range(self.row, self.col, self.col + 1, ch)
            line = self.buffer.get_line(self.row)
        else:
            self.buffer.set_line(self.row, line + ch)
            line = self.buffer.get_line(self.row)
        self.col = min(self.col + 1, len(line))
        self.modified = True

    def delete_word_under_cursor(self) -> None:
        line = self.buffer.get_line(self.row)
        i = self.col
        if i >= len(line) or not _is_word_char(line[i]):
            self.message = "No word under cursor"
            return
        start = i
        while start > 0 and _is_word_char(line[start - 1]):
            start -= 1
        end = i
        while end < len(line) and _is_word_char(line[end]):
            end += 1
        if end < len(line) and line[end].isspace():
            end += 1
        self._push_undo()
        self.buffer.delete_range(self.row, start, end)
        self.col = start
        self.modified = True

    def delete_line(self) -> None:
        self._push_undo()
        if self.buffer.line_count() == 1:
            self.buffer.set_line(0, "")
            self.row = self.col = 0
        else:
            self.buffer.delete_line(self.row)
            if self.row >= self.buffer.line_count():
                self.row = self.buffer.line_count() - 1
            self.col = 0
        self.modified = True

    #   yank / paste  

    def yank_line(self) -> None:
        self.yank.set_line(self.buffer.get_line(self.row))
        self.message = "Line yanked"

    def yank_word(self) -> None:
        line = self.buffer.get_line(self.row)
        i = self.col
        if i >= len(line) or not _is_word_char(line[i]):
            self.message = "No word under cursor"
            return
        start = i
        while start > 0 and _is_word_char(line[start - 1]):
            start -= 1
        end = i
        while end < len(line) and _is_word_char(line[end]):
            end += 1
        self.yank.set_word(line[start:end])
        self.message = f"Word yanked: {line[start:end]}"

    def paste_after(self) -> None:
        text, kind = self.yank.get()
        if not text:
            self.message = "Yank buffer is empty"
            return
        self._push_undo()
        if kind == "line":
            self.buffer.insert_line(self.row + 1, text)
            self.row += 1
            self.col = 0
        else:
            line = self.buffer.get_line(self.row)
            pos = min(self.col + 1, len(line))
            self.buffer.insert_text(self.row, pos, text)
            self.col = pos + len(text)
        self.modified = True
        self.message = "Pasted"

    #   навигация  

    def move_left(self):  self.col = max(0, self.col - 1)
    def move_right(self): self.col = min(len(self.buffer.get_line(self.row)), self.col + 1)
    def move_up(self):    self.row = max(0, self.row - 1); self.clamp()
    def move_down(self):  self.row = min(self.buffer.line_count() - 1, self.row + 1); self.clamp()
    def move_home(self):  self.col = 0
    def move_end(self):   self.col = len(self.buffer.get_line(self.row))

    def page_up(self, page_size: int):
        self.row = max(0, self.row - max(1, page_size)); self.clamp()

    def page_down(self, page_size: int):
        self.row = min(self.buffer.line_count() - 1, self.row + max(1, page_size)); self.clamp()

    def goto_top(self):  self.row = self.col = 0
    def goto_bottom(self): self.row = self.buffer.line_count() - 1; self.col = 0

    def goto_line(self, number: int) -> None:
        self.row = min(max(0, number - 1), self.buffer.line_count() - 1)
        self.col = 0
        self.clamp()

    def move_word_forward(self) -> None:
        line = self.buffer.get_line(self.row)
        n, i = len(line), self.col
        if i < n and _is_word_char(line[i]):
            j = i
            while j + 1 < n and _is_word_char(line[j + 1]):
                j += 1
            if j > i:
                self.col = j
                return
            i = j + 1
        while i < n and not _is_word_char(line[i]):
            i += 1
        if i >= n:
            self.col = n
            return
        j = i
        while j + 1 < n and _is_word_char(line[j + 1]):
            j += 1
        self.col = j

    def move_word_backward(self) -> None:
        line = self.buffer.get_line(self.row)
        i = min(self.col, len(line))
        if i > 0 and _is_word_char(line[i - 1]):
            j = i - 1
            while j > 0 and _is_word_char(line[j - 1]):
                j -= 1
            self.col = j
            return
        j = i - 1
        while j >= 0 and not _is_word_char(line[j]):
            j -= 1
        if j < 0:
            self.col = 0
            return
        while j > 0 and _is_word_char(line[j - 1]):
            j -= 1
        self.col = j

    #   поиск  

    def _advance(self, row, col, forward, lines):
        """Сдвиг на 1 позицию для повторного поиска."""
        if forward:
            col += 1
            if col > len(lines[row]):
                row += 1
                col = 0
            if row >= len(lines):
                row, col = 0, 0
        else:
            if col > 0:
                col -= 1
            elif row > 0:
                row -= 1
                col = len(lines[row])
            if row < 0:
                row = len(lines) - 1
                col = len(lines[row])
        return row, col

    def search(self, query: str, forward: bool = True, repeat: bool = False) -> bool:
        if query:
            self.last_search = query
        else:
            query = self.last_search
        if not query:
            self.message = "No previous search"
            return False

        self.last_search_forward = forward
        lines = self.buffer.all_lines()

        if repeat:
            start_row, start_col = self._advance(self.row, self.col, forward, lines)
        else:
            start_row, start_col = self.row, self.col

        pos = self.search_service.find(lines, start_row, start_col, query, forward)
        if pos is None:
            # циклический переход
            if forward:
                pos = self.search_service.find(lines, 0, 0, query, True)
            else:
                pos = self.search_service.find(
                    lines, len(lines) - 1, len(lines[-1]), query, False
                )
        if pos is None:
            self.message = f"Pattern not found: {query}"
            return False

        self.row, self.col = pos
        return True

    def repeat_search(self, reverse: bool = False) -> bool:
        direction = self.last_search_forward
        if reverse:
            direction = not direction
        return self.search("", direction, repeat=True)

    #   файлы  

    def open_file(self, path: str) -> None:
        lines = self.file_service.load(path)
        self.buffer.restore(lines)
        self.row = self.col = 0
        self.filename = path
        self.modified = False
        self.undo_manager.clear() # ИЗМЕНЕНО
        self.message = f'"{path}" opened'

    def save_file(self, path: Optional[str] = None) -> None:
        target = path if path is not None else self.filename
        if not target:
            raise ValueError("No file name")
        self.file_service.save(target, self.buffer.all_lines())
        if path is not None:
            self.filename = path
        self.modified = False
        self.message = f'"{target}" written'

    def clear_all(self) -> None:
        self.buffer.restore([""])
        self.row = self.col = 0
        self.filename = None
        self.modified = False
        self.undo_manager.clear()
        self.message = "Cleared"

    def toggle_numbers(self) -> None:
        self.show_numbers = not self.show_numbers
        self.message = f"Line numbers: {'on' if self.show_numbers else 'off'}"

    """ Дополнительные задания 1-3"""

    def toggle_syntax_highlight(self) -> None:
        """ Включение / выключение подсветки (доп 2)"""
        self.highlight_syntax = not self.highlight_syntax
        self.message = f"Syntax highlight: {'on' if self.highlight_syntax else 'off'}"

    def number_lines(self) -> None:
        """ Нумерация строк с сохранением (доп 1)"""
        self._push_undo()
        for i in range(self.buffer.line_count()):
            text = self.buffer.get_line(i)
            prefix = f"{i + 1:>4} "
            if not text.startswith(prefix):
                self.buffer.set_line(i, prefix + text)
        self.modified = True
        self.message = "Lines numbered"

    def get_line_obj(self, row: int) -> MyString:
        """Возврат строки в декораторе, если вкл подсветка"""
        obj = self.buffer.get_line_obj(row) if hasattr(self.buffer, 'get_line_obj') else MyString(self.buffer.get_line(row))
        if self.highlight_syntax:
            return SyntaxHighlightDecorator(obj)
        return obj