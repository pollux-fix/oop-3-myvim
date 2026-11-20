from __future__ import annotations


class YankBuffer:
    def __init__(self) -> None:
        self._text = ""
        self._type = "char"  # "line" | "word" | "char"

    def set_line(self, text: str) -> None:
        self._text, self._type = text, "line"

    def set_word(self, text: str) -> None:
        self._text, self._type = text, "word"

    def get(self) -> tuple[str, str]:
        return self._text, self._type

    def is_empty(self) -> bool:
        return not self._text