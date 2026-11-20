import pytest

from myvim.model import EditorModel


# ---------- инициализация ----------

def test_initial_state(model):
    assert model.buffer.line_count() == 1
    assert model.buffer.get_line(0) == ""
    assert (model.row, model.col) == (0, 0)
    assert model.modified is False
    assert model.filename is None
    assert model.show_numbers is False


# ---------- редактирование ----------

def test_insert_char_and_text(model):
    model.insert_char("a")
    model.insert_text("bc")
    assert model.buffer.get_line(0) == "abc"
    assert model.col == 3
    assert model.modified is True


def test_insert_char_rejects_multichar(model):
    with pytest.raises(ValueError):
        model.insert_char("ab")


def test_newline_splits(model):
    model.insert_text("abcdef")
    model.col = 3
    model.newline()
    assert model.buffer.all_lines() == ["abc", "def"]
    assert (model.row, model.col) == (1, 0)


def test_backspace_within_line(model):
    model.insert_text("abc")
    model.backspace()
    assert model.buffer.get_line(0) == "ab"
    assert model.col == 2


def test_backspace_joins_lines(model):
    model.buffer.restore(["abc", "def"])
    model.row, model.col = 1, 0
    model.backspace()
    assert model.buffer.all_lines() == ["abcdef"]
    assert model.row == 0
    assert model.col == 3


def test_backspace_at_buffer_start_noop(model):
    model.backspace()
    assert model.buffer.all_lines() == [""]
    assert model.col == 0


def test_delete_char(model):
    model.insert_text("abc")
    model.col = 1
    model.delete_char()
    assert model.buffer.get_line(0) == "ac"


def test_delete_char_joins_next_line(model):
    model.buffer.restore(["ab", "cd"])
    model.row, model.col = 0, 2
    model.delete_char()
    assert model.buffer.all_lines() == ["abcd"]


def test_clear_current_line(model):
    model.insert_text("abc")
    model.col = 2
    model.clear_current_line()
    assert model.buffer.get_line(0) == ""
    assert model.col == 0


def test_replace_char(model):
    model.insert_text("abc")
    model.col = 1
    model.replace_char("X")
    assert model.buffer.get_line(0) == "aXc"
    assert model.col == 2


def test_replace_char_at_end_appends(model):
    model.insert_text("ab")
    model.col = 2
    model.replace_char("Z")
    assert model.buffer.get_line(0) == "abZ"


# ---------- удаление слов / строк ----------

def test_delete_word_under_cursor(model):
    model.insert_text("hello world")
    model.col = 2
    model.delete_word_under_cursor()
    assert model.buffer.get_line(0) == "world"
    assert model.col == 0


def test_delete_word_not_on_word(model):
    model.insert_text("hello world")
    model.col = 5  # пробел
    model.delete_word_under_cursor()
    assert model.buffer.get_line(0) == "hello world"
    assert "No word" in model.message


def test_delete_line(model):
    model.buffer.restore(["a", "b", "c"])
    model.row = 1
    model.delete_line()
    assert model.buffer.all_lines() == ["a", "c"]
    assert model.row == 1


def test_delete_line_on_last(model):
    model.buffer.restore(["a", "b"])
    model.row = 1
    model.delete_line()
    assert model.buffer.all_lines() == ["a"]
    assert model.row == 0


def test_delete_only_line_leaves_empty(model):
    model.insert_text("only")
    model.delete_line()
    assert model.buffer.all_lines() == [""]
    assert (model.row, model.col) == (0, 0)


# ---------- yank / paste ----------

def test_yank_line_paste(model):
    model.buffer.restore(["one", "two"])
    model.row = 0
    model.yank_line()
    assert model.yank.get() == ("one", "line")
    model.paste_after()
    assert model.buffer.all_lines() == ["one", "one", "two"]
    assert model.row == 1


def test_yank_word_paste(model):
    model.buffer.restore(["alpha beta"])
    model.col = 0
    model.yank_word()
    assert model.yank.get() == ("alpha", "word")
    model.col = 10
    model.paste_after()
    assert "alpha" in model.buffer.get_line(0)


def test_yank_word_not_on_word(model):
    model.insert_text("hi")
    model.col = 5
    model.yank_word()
    assert model.yank.is_empty()
    assert "No word" in model.message


def test_paste_empty_buffer(model):
    model.paste_after()
    assert "empty" in model.message


# ---------- навигация ----------

def test_cursor_left_right_bounds(model):
    model.insert_text("abc")  # col=3
    model.move_right()
    assert model.col == 3
    model.move_left()
    model.move_left()
    model.move_left()
    model.move_left()
    assert model.col == 0


def test_cursor_up_down_with_short_line(model):
    model.buffer.restore(["abcdef", "xy", "long line here"])
    model.row, model.col = 0, 5
    model.move_down()
    assert model.row == 1
    assert model.col == 2   # обрезано до длины короткой строки
    model.move_down()
    assert model.row == 2
    assert model.col == 2
    model.move_up()
    assert model.col == 2


def test_home_end(model):
    model.insert_text("abc")
    model.move_home()
    assert model.col == 0
    model.move_end()
    assert model.col == 3


def test_word_moves(model):
    model.insert_text("hello world foo")
    model.col = 0
    model.move_word_forward()
    assert model.col == 4
    model.move_word_forward()
    assert model.col == 10
    model.move_word_backward()
    assert model.col == 6
    model.move_word_backward()
    assert model.col == 0


def test_goto_top_bottom(model):
    model.buffer.restore(["a", "b", "c"])
    model.goto_bottom()
    assert model.row == 2
    model.goto_top()
    assert model.row == 0
    assert model.col == 0


def test_goto_line(model):
    model.buffer.restore(["a", "b", "c", "d"])
    model.goto_line(3)
    assert model.row == 2
    model.goto_line(100)
    assert model.row == 3   # clamped
    model.goto_line(-5)
    assert model.row == 0


def test_page_up_down(model):
    model.buffer.restore([str(i) for i in range(100)])
    model.row = 50
    model.page_up(10)
    assert model.row == 40
    model.page_down(10)
    assert model.row == 50
    model.page_down(1000)
    assert model.row == 99


# ---------- undo ----------

def test_undo_single(model):
    model.insert_text("abc")
    model.undo()
    assert model.buffer.get_line(0) == ""


def test_undo_stack_empty(model):
    model.undo()
    assert "Nothing" in model.message


def test_undo_line(model):
    model.insert_text("abc")
    model.begin_line_edit()
    model.insert_text("XYZ")
    model.undo_line()
    assert model.buffer.get_line(0) == "abc"


def test_undo_line_without_snapshot(model):
    model.undo_line()
    assert "Nothing" in model.message


# ---------- поиск ----------

def test_search_forward(model):
    model.buffer.restore(["alpha", "beta", "gamma"])
    model.row = model.col = 0
    assert model.search("beta", forward=True) is True
    assert model.row == 1


def test_search_backward(model):
    model.buffer.restore(["alpha", "beta", "gamma"])
    model.row, model.col = 2, 0
    assert model.search("alpha", forward=False) is True
    assert model.row == 0


def test_search_wraps_forward(model):
    model.buffer.restore(["x", "target", "x"])
    model.row, model.col = 1, 1
    # от позиции 1 в "target" — не найдём до конца, но обернёмся
    assert model.search("target", forward=True) is True
    assert (model.row, model.col) == (1, 0)


def test_search_not_found(model):
    model.buffer.restore(["a", "b"])
    assert model.search("zzz", forward=True) is False
    assert "not found" in model.message


def test_search_no_query(model):
    assert model.search("", forward=True) is False
    assert "previous" in model.message


def test_search_repeat_forward(model):
    model.buffer.restore(["t", "t", "t"])
    model.row = model.col = 0
    model.search("t", forward=True)    # → (0,0)
    model.repeat_search(False)          # → (1,0)
    model.repeat_search(False)          # → (2,0)
    assert model.row == 2


def test_search_repeat_backward(model):
    model.buffer.restore(["t", "t", "t"])
    model.row, model.col = 2, 0
    model.search("t", forward=False)
    model.repeat_search(True)   # N — разворот
    # направление перевернулось — пойдёт вперёд


# ---------- файлы ----------

def test_save_and_open(model, tmp_path):
    p = tmp_path / "f.txt"
    model.insert_text("hello")
    model.save_file(str(p))
    assert model.modified is False
    assert model.filename == str(p)

    m2 = EditorModel()
    m2.open_file(str(p))
    assert m2.buffer.get_line(0) == "hello"
    assert m2.modified is False


def test_save_as(model, tmp_path):
    p = tmp_path / "new.txt"
    model.insert_text("x")
    model.save_file(str(p))
    assert model.filename == str(p)


def test_save_no_filename():
    m = EditorModel()
    with pytest.raises(ValueError):
        m.save_file()


def test_clear_all(model):
    model.insert_text("abc")
    model.filename = "x"
    model.clear_all()
    assert model.buffer.all_lines() == [""]
    assert model.filename is None
    assert model.modified is False


def test_toggle_numbers(model):
    assert model.show_numbers is False
    model.toggle_numbers()
    assert model.show_numbers is True
    model.toggle_numbers()
    assert model.show_numbers is False


def test_modified_flag_on_edit(model):
    assert model.modified is False
    model.insert_char("a")
    assert model.modified is True