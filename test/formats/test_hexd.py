import io

import pytest

from lib.file_format.hexd import FileFormat


encoded_data = """000d2f 99
000d30 10
300000 20
"""


decoded_dict = {
    0xd2f: 0x99,
    0xd30: 0x10,
    0x300000: 0x20,
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
    with pytest.raises(ValueError):
        assert run_decode("00")
