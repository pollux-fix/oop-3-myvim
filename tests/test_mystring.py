import pytest

from myvim.mystring import MyString


def test_construct_from_str():
    assert MyString("abc").to_py() == "abc"


def test_construct_from_bytes():
    assert MyString(b"abc").to_py() == "abc"


def test_roundtrip_latin1():
    s = MyString("Привет")  # не влезет в latin-1
    with pytest.raises(UnicodeEncodeError):
        s.to_bytes()

    s2 = MyString("café")
    assert s2.to_bytes() == b"caf\xe9"
    assert MyString(s2.to_bytes()).to_py() == "café"


def test_len_and_index():
    s = MyString("abc")
    assert len(s) == 3
    assert s[0] == "a"
    assert s[-1] == "c"


def test_setitem():
    s = MyString("abc")
    s[1] = "X"
    assert str(s) == "aXc"


def test_setitem_rejects_multichar():
    s = MyString("abc")
    with pytest.raises(ValueError):
        s[0] = "XY"


def test_eq_and_add():
    assert MyString("a") == MyString("a")
    assert MyString("a") == "a"
    assert (MyString("a") + "b").to_py() == "ab"


def test_iadd():
    s = MyString("a")
    s += "b"
    assert str(s) == "ab"


def test_insert_erase_replace():
    s = MyString("hello")
    s.insert(5, " world")
    assert str(s) == "hello world"
    s.erase(5, 6)
    assert str(s) == "hello"
    s.replace(0, 5, "HI")
    assert str(s) == "HI"


def test_substr():
    s = MyString("abcdef")
    assert s.substr(2, 3).to_py() == "cde"
    assert s.substr(4).to_py() == "ef"


def test_find():
    s = MyString("abcabc")
    assert s.find("bc") == 1
    assert s.find("bc", 2) == 4
    assert s.find("zz") == -1


def test_repr():
    assert repr(MyString("x")) == "MyString('x')"