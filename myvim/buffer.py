from __future__ import annotations

from .interfaces import ITextBuffer
from .mystring import MyString


class TextBuffer(ITextBuffer):
    """Только хранит строки и выполняет атомарные операции над ними."""

    def __init__(self, initial_lines: list[str] | None = None) -> None:
        if initial_lines is None:
            initial_lines = [""]
        self._lines: list[MyString] = [MyString(s) for s in initial_lines]

    def line_count(self) -> int:
        return len(self._lines)

    def get_line(self, row: int) -> str:
        return self._lines[row].to_py()

    def set_line(self, row: int, text: str) -> None:
        self._lines[row] = MyString(text)

    def insert_line(self, row: int, text: str) -> None:
        self._lines.insert(row, MyString(text))

    def delete_line(self, row: int) -> None:
        del self._lines[row]
        if not self._lines:
            self._lines.append(MyString(""))

    def insert_text(self, row: int, col: int, text: str) -> None:
        self._lines[row].insert(col, text)

    def delete_range(self, row: int, start: int, end: int) -> str:
        removed = self._lines[row].substr(start, end - start).to_py()
        self._lines[row].erase(start, end - start)
        return removed

    def replace_range(self, row: int, start: int, end: int, text: str) -> None:
        self._lines[row].replace(start, end - start, text)

    def all_lines(self) -> list[str]:
        return [str(x) for x in self._lines]

    def restore(self, lines: list[str]) -> None:
        self._lines = [MyString(s) for s in lines]