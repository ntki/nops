import io

import pytest

from lib.file_format.inhx32 import FileFormat


encoded_data = """:020000040000FA
:0400000074EF04F0A5
:0400080018EF02F0FB
:06002A00D9CFE5FFE1CF94
:0C0D2000010240000007058102400000B5
:020000040030CA
:0E000000203EF8FEFFFF9FFFFFFFFFFFFFFF08
:00000001FF
"""

decoded_dict = {
    0x0: 0x74,
    0x1: 0xef,
    0x2: 0x4,
    0x3: 0xf0,
    0x8: 0x18,
    0x9: 0xef,
    0xa: 0x2,
    0xb: 0xf0,
    0x2a: 0xd9,
    0x2b: 0xcf,
    0x2c: 0xe5,
    0x2d: 0xff,
    0x2e: 0xe1,
    0x2f: 0xcf,
    0xd20: 0x1,
    0xd21: 0x2,
    0xd22: 0x40,
    0xd23: 0x0,
    0xd24: 0x0,
    0xd25: 0x7,
    0xd26: 0x5,
    0xd27: 0x81,
    0xd28: 0x2,
    0xd29: 0x40,
    0xd2a: 0x0,
    0xd2b: 0x0,
    0x300000: 0x20,
    0x300001: 0x3e,
    0x300002: 0xf8,
    0x300003: 0xfe,
    0x300004: 0xff,
    0x300005: 0xff,
    0x300006: 0x9f,
    0x300007: 0xff,
    0x300008: 0xff,
    0x300009: 0xff,
    0x30000a: 0xff,
    0x30000b: 0xff,
    0x30000c: 0xff,
    0x30000d: 0xff,
}


def run_decode(string):
    return FileFormat().deserialize(io.StringIO(string))


def run_encode(data_dict):
    return "".join(FileFormat().serialize(data_dict))


def test_decode():
    assert decoded_dict == run_decode(encoded_data)


def test_encode():
    assert encoded_data == run_encode(decoded_dict)


def test_malformed():
    with pytest.raises(ValueError):
        assert run_decode("invalid")


def test_crc_error():
    with pytest.raises(ValueError):
        assert run_decode(":0400080018EF02F011")


def test_rectype_error():
    with pytest.raises(ValueError):
        assert run_decode(":040000AA00000000FB")
