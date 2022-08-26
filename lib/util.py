from typing import Iterator, List
import itertools
import string

from lib.interfaces import Mem


def split_to_pages(mem: Mem, page_size: int) -> Iterator[Mem]:
    """
    Groups mem by key // page_size.

    :param mem: dict holding (address: value) pairs
    :type mem: Mem
    :param page_size: size of the address space for one group
    :type page_size: int

    :return: iterator of subgroup dicts
    :rtype: Iterator[Mem]
    """
    assert isinstance(mem, dict)
    assert isinstance(page_size, int)

    for _, items in itertools.groupby(
            sorted(mem.items()),
            lambda item: item[0] // page_size):
        yield dict(items)


def split_on_gaps(mem: Mem) -> Iterator[Mem]:
    """
    Yields subdictionaries of contiguous keys.

    :param mem: dict holding (address: value) pairs
    :type mem: Mem

    :return: iterator of subdicts
    :rtype: Iterator[Mem]
    """
    assert isinstance(mem, dict)

    last, subseq_id = None, None

    def grouper(item):
        nonlocal last, subseq_id
        key, _value = item
        if key - 1 != last:
            subseq_id = key
        last = key
        return subseq_id

    for _, items in itertools.groupby(
            sorted(mem.items()),
            grouper):
        yield dict(items)


def cmd(pattern: str, **kwargs) -> List[int]:
    """
    Fills a bitpattern with given values.

    pattern is a string of the following characters:
      0, 1: treated literally
      a-z: placeholders for the bits of ints given as keyword arguments
      _: becomes a 0
      whitespace: ignored

    :param pattern: bitpattern
    :type pattern: str
    :param \**kwargs: int arguments corresponding the placeholders in pattern

    :return: list of bits
    :rtype: [int]
    """
    assert all(c in "01_ " + string.ascii_lowercase for c in pattern)
    assert all(k in string.ascii_lowercase for k in kwargs.keys())

    pattern = pattern.replace(" ", "").replace("_", "0").replace("x", "0")
    bits = []
    for c in reversed(pattern):
        if c in "01":
            bits.append(int(c))
        else:
            bits.append(kwargs[c] & 1)
            kwargs[c] >>= 1
    for k, v in kwargs.items():
        if v:
            raise ValueError(f"'{k}' is out of bounds")
    bits.reverse()
    return bits


def reverse(value: int, bit_length: int) -> int:
    """
    Bitwise reverses the given value

    :param value: value to rotate
    :type value: int
    :param bit_length: intended bit length of value
    :type bit_length: int

    :return: reversed value
    :type: int
    """
    assert bit_length >= value.bit_length()

    result = 0
    for _ in range(bit_length):
        result <<= 1
        result |= value & 1
        value >>= 1
    return result
