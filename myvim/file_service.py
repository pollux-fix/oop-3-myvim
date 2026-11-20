from __future__ import annotations

from .interfaces import IFileService


class FileService(IFileService):
    def __init__(self, encoding: str = "latin-1") -> None:
        self._encoding = encoding

    def load(self, path: str) -> list[str]:
        with open(path, "r", encoding=self._encoding, newline="") as f:
            text = f.read()
        lines = text.split("\n")
        if text.endswith("\n"):
            lines = lines[:-1]
        if not lines:
            lines = [""]
        return lines

    def save(self, path: str, lines: list[str]) -> None:
        text = "\n".join(lines)
        with open(path, "w", encoding=self._encoding, newline="") as f:
            f.write(text)
            if text:
                f.write("\n")