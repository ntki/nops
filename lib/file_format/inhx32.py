import enum

from lib import util
from lib.interfaces import BaseFileFormat


class Rectype(enum.Enum):
    DATA = 0
    EOF = 1
    EXTENDED_SEGMENT_ADDRESS = 2
    START_SEGMENT_ADDRESS = 3
    EXTENDED_LINEAR_ADDRESS = 4
    START_LINEAR_ADDRESS = 5


def crc(*data):
    sum_ = 0
    for b in data:
        while b:
            sum_ += b
            b >>= 8
    return (0x100 - (sum_ & 0xff)) & 0xff


def format_record(rectype, offset, data):
    offset &= 0xffff
    datalen = len(data)
    chksum = crc(datalen, rectype.value, offset, *data)
    data = bytearray(data).hex().upper()
    return f":{datalen:02X}{offset:04X}{rectype.value:02X}{data}{chksum:02X}\n"


class FileFormat(BaseFileFormat):
    "Intel Hex 32 format."

    def deserialize(self, reader):
        result = {}
        base_address = 0

        for lineno, line in enumerate(reader.readlines(), 1):
            line = line.strip()
            record = bytearray.fromhex(line[1:])
            if not record:
                continue
            _datalen, ahigh, alow, rectype, *data, chksum = record
            rectype = Rectype(rectype)
            offset = (ahigh << 8) + alow

            if chksum != crc(*record[:-1]):
                raise ValueError(f"CRC Error on line({lineno}): {line}")

            if rectype == Rectype.DATA:
                result.update(enumerate(data, base_address + offset))
            elif rectype == Rectype.EXTENDED_SEGMENT_ADDRESS:
                base_address = ((data[0] << 8) + data[1]) << 4
            elif rectype == Rectype.EXTENDED_LINEAR_ADDRESS:
                base_address = ((data[0] << 8) + data[1]) << 16
        return dict(sorted(result.items()))

    def serialize(self, mem):
        address_extension = None
        for page in util.split_to_pages(mem, 16):
            for subpage in util.split_on_gaps(page):
                slice_address = min(subpage)
                high_address = slice_address.to_bytes(4, 'big')[:2]
                if address_extension != high_address:
                    address_extension = high_address
                    yield format_record(
                        Rectype.EXTENDED_LINEAR_ADDRESS,
                        0,
                        high_address)
                yield format_record(
                    Rectype.DATA,
                    slice_address,
                    subpage.values())
        yield format_record(Rectype.EOF, 0, [])
