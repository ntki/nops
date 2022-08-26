from lib import util
from lib.interfaces import BaseFileFormat


class FileFormat(BaseFileFormat):
    """Default hexdump format"""

    def deserialize(self, reader):
        result = {}
        for lineno, line in enumerate(reader.readlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                address, data = line.split(" ", 1)
                address = int(address, 16)
                data = bytes.fromhex(data)
            except ValueError:
                raise ValueError(f"Invalid line({lineno}): {line}")
            result.update(enumerate(data, address))
        return dict(sorted(result.items()))

    def serialize(self, mem):
        if not mem:
            return ""
        max_addr_len = (max(mem).bit_length() + 3) // 4

        for page in util.split_to_pages(mem, 16):
            for subpage in util.split_on_gaps(page):
                slice_address = min(subpage)
                data = bytes(subpage.values()).hex().lower()
                yield f"{slice_address:0{max_addr_len}x} {data}\n"
