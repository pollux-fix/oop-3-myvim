from __future__ import annotations

from typing import Any

from .interfaces import IUndoService


class UndoManager(IUndoService):
    def __init__(self, max_size: int = 500) -> None:
        self._stack: list[Any] = []
        self._max = max_size

    def push(self, snapshot: Any) -> None:
        self._stack.append(snapshot)
        if len(self._stack) > self._max:
            self._stack.pop(0)

    def pop(self) -> Any:
        if not self._stack:
            return None
        return self._stack.pop()

    def clear(self) -> None:
        self._stack.clear()

    def is_empty(self) -> bool:
        return not self._stack