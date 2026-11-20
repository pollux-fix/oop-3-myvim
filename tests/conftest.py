import pytest

from myvim.buffer import TextBuffer
from myvim.file_service import FileService
from myvim.model import EditorModel
from myvim.search import SearchEngine
from myvim.undo import UndoManager


@pytest.fixture
def model():
    """Свежая модель без текста."""
    return EditorModel(
        buffer=TextBuffer(),
        file_service=FileService(),
        undo=UndoManager(),
        search=SearchEngine(),
    )


@pytest.fixture
def model_with_text(model):
    """Модель с тремя строками текста."""
    model.buffer.restore(["hello world", "second line", "third line"])
    return model