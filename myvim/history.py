from __future__ import annotations

class CommandHistory:
    """Паттерн Singletone для хранения истории введенных команд"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._history = []  # list[str]
        return cls._instance
    
    def add(self, cmd: str) -> None:
        if cmd and (not self._history or self._history[-1] != cmd):
            self._history.append(cmd)

    def get_last(self, count: int = 5) -> list[str]:
        return self._history[-count:]
    
    def clear(self) -> None:
        self._history.clear()