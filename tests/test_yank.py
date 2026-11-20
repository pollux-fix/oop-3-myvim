from myvim.yank import YankBuffer


def test_empty_default():
    y = YankBuffer()
    assert y.is_empty()
    assert y.get() == ("", "char")


def test_set_line():
    y = YankBuffer()
    y.set_line("abc")
    assert not y.is_empty()
    assert y.get() == ("abc", "line")


def test_set_word():
    y = YankBuffer()
    y.set_word("word")
    assert y.get() == ("word", "word")