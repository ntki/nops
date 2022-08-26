import pytest

from lib.util import split_to_pages, split_on_gaps, cmd, reverse


d = {0: 0, 1: 1, 2: 2, 5: 5}


def test_split_to_pages():
    assert list(split_to_pages({}, 8)) == []
    assert list(split_to_pages(d, 2)) == [{0: 0, 1: 1}, {2: 2}, {5: 5}]
    assert list(split_to_pages(d, 4)) == [{0: 0, 1: 1, 2: 2}, {5: 5}]
    assert list(split_to_pages(d, 8)) == [{0: 0, 1: 1, 2: 2, 5: 5}]


def test_split_on_gaps():
    assert list(split_on_gaps({})) == []
    assert list(split_on_gaps(d)) == [{0: 0, 1: 1, 2: 2}, {5: 5}]


def test_cmd():
    assert cmd("") == []
    assert cmd("1") == [1]
    assert cmd("01") == [0, 1]
    assert cmd("a_a", a=2) == [1, 0, 0]
    assert cmd("aaa1 bbbb", a=2, b=15) == [0, 1, 0, 1, 1, 1, 1, 1]

    with pytest.raises(KeyError):
        cmd("aa", b=2)

    with pytest.raises(ValueError):
        cmd("aa", a=20)

    with pytest.raises(AssertionError):
        cmd("Aa", a=0)


def test_reverse():
    assert reverse(0, 0) == 0
    assert reverse(0, 64) == 0
    assert reverse(0b0110, 7) == 0b0110_000
    assert reverse(0xaa55, 16) == 0xaa55
    assert reverse(0x755, 12) == 0xaae

    with pytest.raises(AssertionError):
        reverse(1, 0)
