import dataclasses
import logging

from lib import util
from lib.targetop import TargetOp


logger = logging.getLogger(__name__)


@dataclasses.dataclass
class Device:
    name: str
    flash_size: int
    page_size: int
    eeprom_size: int


DEVICE_SIGNATURES = {
    (0x1f, 0x9403, 0x1e, 0x94, 3): Device("atmega16a", 2**14, 128, 512),
    (0x1f, 0x9502, 0x1e, 0x95, 2): Device("atmega32a", 2**15, 128, 1024),
}


RESET = "RESET"
TCK = "TCK"
TMS = "TMS"
TDI = "TDI"
TDO = "TDO"

EXTEST = 0
IDCODE = 1
SAMPLE_PRELOAD = 2
BYPASS = 0xf
AVR_RESET = 0xc
PROG_ENABLE = 4
PROG_COMMANDS = 5
PROG_PAGELOAD = 6
PROG_PAGEREAD = 7
PRIVATE1 = 8
PRIVATE2 = 9
PRIVATE3 = 0xa
PRIVATE4 = 0xb


class Jtag:
    def __init__(self, pinproxy):
        self.pinproxy = pinproxy

    def shift_ir(self, tdi_seq, read_bits=()):
        self._change_state((1, 1, 0))  # Capture-IR
        self._shift_register(tdi_seq, read_bits)  # Exit1-xR
        self._change_state((1, 0))  # Idle

    def shift_dr(self, tdi_seq, read_bits=()):
        self._change_state((1, 0))  # Capture-DR
        self._shift_register(tdi_seq, read_bits)
        self._change_state((1, 0))  # Idle

    def reset_to_idle(self):
        self._change_state([1] * 5 + [0])

    def pop_fetched(self, *args, **kwargs):
        return self.pinproxy.pop_fetched(*args, **kwargs)

    def _change_state(self, tms_seq):
        p = self.pinproxy
        for b in tms_seq:
            p.set_pin(TMS, b)
            p.set_pin(TCK)
            p.reset_pin(TCK)

    # TDI on loop/leave rising edge, TDO on enter/loop falling edge
    def _shift_register(self, tdi_seq, read_bits=()):
        p = self.pinproxy
        tms_seq = [0] * len(tdi_seq) + [1]  # ->Exit1 with last bit
        tdi_seq = list(tdi_seq) + [0]
        for i, tms in enumerate(tms_seq):
            p.set_pin(TDI, tdi_seq.pop())
            p.set_pin(TMS, tms)
            p.set_pin(TCK)
            p.reset_pin(TCK)
            if i in read_bits:
                p.fetch_pin(TDO)


class AvrJtag:
    def __init__(self, jtag):
        self.jtag = jtag

    def avr_reset(self, on=1):
        self.jtag.shift_ir(util.cmd("cccc", c=AVR_RESET))
        self.jtag.shift_dr([bool(on)])

    def prog_enable(self, enable=True):
        self.jtag.shift_ir(util.cmd("cccc", c=PROG_ENABLE))
        if enable:
            self.jtag.shift_dr((1,0,1,0, 0,0,1,1, 0,1,1,1, 0,0,0,0))
        else:
            self.jtag.shift_dr((0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,0))

    def prog_commands(self):
        self.jtag.shift_ir(util.cmd("cccc", c=PROG_COMMANDS))

    def prog_pageread(self):
        self.jtag.shift_ir(util.cmd("cccc", c=PROG_PAGEREAD))

    def prog_pageload(self):
        self.jtag.shift_ir(util.cmd("cccc", c=PROG_PAGELOAD))

    def get_idcode(self):
        self.jtag.shift_ir(util.cmd("cccc", c=IDCODE))
        self.jtag.shift_dr([0] * 32, range(32))

        idcode = self.jtag.pop_fetched(TDO, 32, lsb=True)[0]
        version = idcode >> 28
        partno = (idcode >> 12) & 0xffff
        manufacturer_id = (idcode >> 1) & 0x7ff
        return manufacturer_id, partno, version

    def write_flash_page(self):  # 2g
        self.jtag.shift_dr((0,1,1,0,1,1,1, 0,0,0,0,0,0,0,0))
        self.jtag.shift_dr((0,1,1,0,1,0,1, 0,0,0,0,0,0,0,0))
        self.jtag.shift_dr((0,1,1,0,1,1,1, 0,0,0,0,0,0,0,0))
        self.jtag.shift_dr((0,1,1,0,1,1,1, 0,0,0,0,0,0,0,0))
        self.jtag.pinproxy.wait(.0045)

    def chip_erase(self):  # 1a
        self.jtag.shift_dr((0,1,0,0,0,1,1, 1,0,0,0,0,0,0,0))
        self.jtag.shift_dr((0,1,1,0,0,0,1, 1,0,0,0,0,0,0,0))
        self.jtag.shift_dr((0,1,1,0,0,1,1, 1,0,0,0,0,0,0,0))
        self.jtag.shift_dr((0,1,1,0,0,1,1, 1,0,0,0,0,0,0,0))
        self.jtag.pinproxy.wait(.009)

    def enter_flash_write(self):  # 2a
        self.jtag.shift_dr((0,1,0,0,0,1,1, 0,0,0,1,0,0,0,0))

    def enter_flash_read(self):  # 3a
        self.jtag.shift_dr((0,1,0,0,0,1,1, 0,0,0,0,0,0,1,0))

    def load_address(self, address):  # 2b 2c 3b 3c
        ab = util.cmd("a" * 16, a=address)
        self.jtag.shift_dr([0,0,0,0,1,1,1] + ab[:8])  # address highbyte
        self.jtag.shift_dr([0,0,0,0,0,1,1] + ab[8:])  # address lowbyte

    def read_signature_bytes(self):
        self.jtag.shift_dr((0,1,0,0,0,1,1, 0,0,0,0,1,0,0,0))  # enable sigbytes

        self.jtag.shift_dr((0,0,0,0,0,1,1, 0,0,0,0,0,0,0,0))  # loadaddress
        self.jtag.shift_dr((0,1,1,0,0,1,0, 0,0,0,0,0,0,0,0))  # read
        self.jtag.shift_dr((0,1,1,0,0,1,1, 0,0,0,0,0,0,0,0), range(8))

        self.jtag.shift_dr((0,0,0,0,0,1,1, 0,0,0,0,0,0,0,1))  # loadaddress
        self.jtag.shift_dr((0,1,1,0,0,1,0, 0,0,0,0,0,0,0,0))  # read
        self.jtag.shift_dr((0,1,1,0,0,1,1, 0,0,0,0,0,0,0,0), range(8))

        self.jtag.shift_dr((0,0,0,0,0,1,1, 0,0,0,0,0,0,1,0))  # loadaddress
        self.jtag.shift_dr((0,1,1,0,0,1,0, 0,0,0,0,0,0,0,0))  # read
        self.jtag.shift_dr((0,1,1,0,0,1,1, 0,0,0,0,0,0,0,0), range(8))

        return self.pop_fetched(TDO, 8, lsb=True)

    def read_page(self):
        self.jtag.shift_dr([0] * 1032, range(8, 1032))

    def write_page(self, tdi_seq):
        self.jtag.shift_dr(tdi_seq)

    def pop_fetched(self, *args, **kwargs):
        return self.jtag.pop_fetched(*args, **kwargs)


def open_device(pinproxy):
    p = pinproxy
    p.set_as_input(TDO)
    for pin in (RESET, TMS, TCK, TDI):
        p.set_as_output(pin)
        p.reset_pin(pin)

    p.set_pin(RESET)
    p.wait(0.01)
    p.reset_pin(RESET)
    p.wait(0.025)

    j = Jtag(p)
    j.reset_to_idle()
    aj = AvrJtag(j)

    mid, pno, ver = aj.get_idcode()
    aj.avr_reset()
    aj.prog_enable()
    aj.prog_commands()
    a, b, c = aj.read_signature_bytes()
    model_key = (mid, pno, a, b, c)
    model = DEVICE_SIGNATURES[model_key]
    logger.info(f"Detected: {model} version: {ver}")

    return aj, model


@TargetOp
def read_flash(pinproxy, progressbar):
    aj, model = open_device(pinproxy)
    aj.enter_flash_read()

    for address in range(0, model.flash_size // 2, model.page_size // 2):
        aj.prog_commands()
        aj.load_address(address)
        aj.prog_pageread()
        aj.read_page()
        progressbar.update(address, model.flash_size // 2)

    aj.prog_commands()
    aj.prog_enable(False)
    aj.avr_reset(0)

    return dict(enumerate(aj.pop_fetched(TDO, lsb=True)))


@TargetOp
def chip_erase(pinproxy):
    aj, _ = open_device(pinproxy)
    aj.chip_erase()


@TargetOp
def write_flash(pinproxy, progressbar, mem):
    aj, model = open_device(pinproxy)

    aj.enter_flash_write()

    for address in range(0, model.flash_size, model.page_size):
        bits = []
        for i in range(address, address + model.page_size):
            v = mem.get(i, 0xff)
            rv = util.reverse(v, 8)
            bits += util.cmd("dddddddd", d=rv)
        bits.reverse()

        aj.load_address(address // 2)  # 2bc
        aj.prog_pageload()
        aj.write_page(bits)
        aj.prog_commands()
        aj.write_flash_page()
        progressbar.update(address, model.flash_size)

    aj.prog_commands()
    aj.prog_enable(False)
    aj.avr_reset(0)
