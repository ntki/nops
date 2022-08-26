import dataclasses
import logging

from lib.targetop import TargetOp
from lib import util

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Device:
    name: str
    flash_size: int
    page_size: int
    eeprom_size: int


DEVICE_SIGNATURES = {
    (0x1e, 0x91, 0x0a): Device("attiny2313", 2**11, 32, 128),
    (0x1e, 0x94, 0x03): Device("atmega16a", 2**14, 128, 512),
    (0x1e, 0x95, 0x02): Device("atmega32a", 2**15, 128, 1024),
}

RESET = "RESET"
SCK = "SCK"
MISO = "MISO"
MOSI = "MOSI"

TWD_FLASH = 4.5e-3
TWD_FUSE = 4.5e-3
TWD_EEPROM = 9e-3
TWD_ERASE = 9e-3

PROGRAMMING_ENABLED = 0x53
SPI_PROGRAMMING_ENABLE =        "1010 1100 0101 0011 ____ ____ ____ ____"
SPI_CHIP_ERASE =                "1010 1100 1000 0000 xxxx xxxx xxxx xxxx"
SPI_READ_PROGRAM_MEMORY =       "0010 h000 aaaa aaaa aaaa aaaa 0000 0000"
SPI_LOAD_PROGRAM_MEMORY_PAGE =  "0100 h000 00__ ____ __aa aaaa iiii iiii"
SPI_WRITE_PROGRAM_MEMORY_PAGE = "0100 1100 00aa aaaa aaaa aaaa ____ ____"
SPI_READ_SIGNATURE_BYTE =       "0011 0000 0000 0000 0000 00aa 0000 0000"


class Avr:
    def __init__(self, pinproxy, progressbar):
        self.pinproxy = pinproxy
        self.progressbar = progressbar
        self.device = None

    def read_flash(self):
        self._open()
        for address in range(self.device.flash_size):
            self.progressbar.update(address, self.device.flash_size)
            spi_command = util.cmd(
                SPI_READ_PROGRAM_MEMORY,
                h=address & 1,
                a=address >> 1)
            self._spi(spi_command, range(24, 32))
        return dict(enumerate(self.pinproxy.pop_fetched(MISO)))

    def write_flash(self, mem):
        self._open()
        if max(mem) >= self.device.flash_size:
            logger.warning(f"device flash size ({self.device.flash_size}) < "
                            f"input data max address ({max(mem)})")  # TODO fixme >=
            mem = {a: v for a, v in mem.items() if a < self.device.flash_size}

        page_size = self.device.page_size
        for page in util.split_to_pages(mem, page_size):
            for byte_address, value in page.items():
                offset = byte_address % page_size
                spi_command = util.cmd(
                    SPI_LOAD_PROGRAM_MEMORY_PAGE,
                    h=offset & 1,
                    a=offset >> 1,
                    i=value)
                self._spi(spi_command)
                self.progressbar.update(byte_address, self.device.flash_size)
            wpage = byte_address // page_size * page_size // 2
            self._spi(util.cmd(SPI_WRITE_PROGRAM_MEMORY_PAGE, a=wpage))
            self.pinproxy.wait(TWD_FLASH)

    def chip_erase(self):
        self._open()
        self._spi(util.cmd(SPI_CHIP_ERASE))
        self.progressbar.update(1, 2)
        self.pinproxy.wait(TWD_ERASE)

    def _open(self):
        if self.device:
            return

        p = self.pinproxy
        p.set_as_input(MISO)
        for pin in (RESET, SCK, MOSI):
            p.set_as_output(pin)
            p.reset_pin(pin)
        p.set_pin(RESET)
        p.wait(0.01)
        p.reset_pin(RESET)
        p.wait(0.025)

        self._spi(util.cmd(SPI_PROGRAMMING_ENABLE), range(16, 24))
        is_sync = self.pinproxy.pop_fetched(MISO)[0]
        if is_sync != PROGRAMMING_ENABLED:
            raise Exception(f"Out of sync ({is_sync:02x})!")
        logger.info("Programming enabled")

        for i in range(3):
            cmd = util.cmd(SPI_READ_SIGNATURE_BYTE, a=i)
            self._spi(cmd, range(24, 32))
        sigbytes = self.pinproxy.pop_fetched(MISO)
        self.device = DEVICE_SIGNATURES[tuple(sigbytes)]
        logger.info(f"Detected: {self.device}")

    def _spi(self, command, read_range=()):
        assert len(command) == 32
        set_pin = self.pinproxy.set_pin
        fetch_pin = self.pinproxy.fetch_pin
        wait = self.pinproxy.wait

        for i, bit in enumerate(command):
            wait(500e-9)
            set_pin(MOSI, bit)
            wait(500e-9)
            set_pin(SCK, True)
            wait(500e-9)
            if i in read_range:
                fetch_pin(MISO)
            wait(500e-9)
            set_pin(SCK, False)


@TargetOp
def read_flash(pinproxy, progressbar):
    return Avr(pinproxy, progressbar).read_flash()


@TargetOp
def write_flash(pinproxy, progressbar, mem):
    return Avr(pinproxy, progressbar).write_flash(mem)


@TargetOp
def chip_erase(pinproxy, progressbar):
    return Avr(pinproxy, progressbar).chip_erase()
