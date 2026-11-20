from __future__ import annotations


class MyString:
    """Обёртка над 1-байтовой строкой (latin-1)."""

    def __init__(self, value: str | bytes = "") -> None:
        if isinstance(value, bytes):
            value = value.decode("latin-1")
        self._s = str(value)

    def to_py(self) -> str:  return self._s
    def to_bytes(self) -> bytes: return self._s.encode("latin-1")
    def __str__(self) -> str: return self._s
    def __repr__(self) -> str: return f"MyString({self._s!r})"
    def __len__(self) -> int: return len(self._s)
    def __getitem__(self, i): return self._s[i]

    def __setitem__(self, i, ch):
        if len(ch) != 1:
            raise ValueError("single character expected")
        chars = list(self._s)
        chars[i] = ch
        self._s = "".join(chars)

    def __eq__(self, other) -> bool: return self._s == str(other)
    def __add__(self, other): return MyString(self._s + str(other))

    def __iadd__(self, other):
        self._s += str(other)
        return self

    def insert(self, index: int, text) -> None:
        text = str(text)
        self._s = self._s[:index] + text + self._s[index:]

    def erase(self, index: int, count: int = 1) -> None:
        self._s = self._s[:index] + self._s[index + count:]

    def replace(self, index: int, count: int, text) -> None:
        text = str(text)
        self._s = self._s[:index] + text + self._s[index + count:]

    def substr(self, index: int, count: int | None = None):
        if count is None:
            return MyString(self._s[index:])
        return MyString(self._s[index:index + count])

    def find(self, sub, start: int = 0) -> int:
        return self._s.find(str(sub), start)