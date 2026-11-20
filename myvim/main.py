from __future__ import annotations

import curses
import sys

from .buffer import TextBuffer
from .commands import create_default_registry
from .controller import EditorController
from .curses_adapter import CursesAdapter
from .file_service import FileService
from .model import EditorModel
from .search import SearchEngine
from .undo import UndoManager
from .view import EditorView


def run() -> None:
    args = sys.argv[1:]
    filename = args[0] if args else None

    def _main(stdscr):
        adapter = CursesAdapter(stdscr)

        # DIP: явная инъекция зависимостей
        model = EditorModel(
            buffer=TextBuffer(),
            file_service=FileService(encoding="latin-1"),
            undo=UndoManager(),
            search=SearchEngine(),
        )

        if filename:
            try:
                model.open_file(filename)
            except Exception as exc:
                model.message = f"Open error: {exc}"

        view = EditorView(adapter)
        registry = create_default_registry()
        controller = EditorController(
            model=model, view=view, input_source=adapter, registry=registry,
        )
        controller.run()

    curses.wrapper(_main)


if __name__ == "__main__":
    run()