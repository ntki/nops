import logging

from lib.targetop import TargetOp

logger = logging.getLogger(__name__)


Twc = 10e-3
Tec = 15e-3
Twl = 30e-3

Tckh = Tckl = 250e-9
Tcss = 50e-9
Tcsh = 0
Tcsl = 250e-9
Tdis = Tdih = 100e-9
Tpd = 400e-9
Tcz = 100e-9
Tsv = 500e-9

CS = "CS"
CLK = "CLK"
DI = "DI"
DO = "DO"
ORG = "ORG"

MODEL_TO_SIZE = {46: 128, 56: 256, 66: 512}


class Ee93lcx6:
    """MicroWire 93LC66 EEPROM
    CS ORG CLK DI DO"""

    def __init__(self, pinproxy, progressbar, model=66):
        self.pinproxy = pinproxy
        self.progressbar = progressbar
        try:
            self.model = int(model)
            self.size = MODEL_TO_SIZE[self.model]
        except (KeyError, ValueError):
            raise ValueError(f"Unknown eeprom model ({model})")

    def read(self):
        self._open()
        for addr in range(self.size):
            self.progressbar.update(addr, self.size)
            self.cmd_read(addr)
        return dict(enumerate(self.pinproxy.pop_fetched(DO)))

    def write(self, mem):
        self._open()
        self.ewen()  # enable write
        if max(mem) >= self.size:
            logger.warning(f"device flash size ({self.size}) < "
                            f"input data max address ({max(mem)})")
            mem = {a: v for a, v in mem.items() if a < self.size}

        length = len(mem)
        for i, (addr, byte) in enumerate(mem.items()):
            self.progressbar.update(i, length)
            if addr < self.size:
                self.cmd_write(addr, byte)
        self.ewds()  # disable write

    def erase(self):
        self._open()
        self.progressbar.update(0, 4)
        self.ewen()
        self.progressbar.update(1, 4)
        self.eral()
        self.progressbar.update(2, 4)
        self.ewds()
        self.progressbar.update(3, 4)

    def _open(self):
        self.pinproxy.set_as_input(DO)
        # 8 bit ORG
        for pin in (CS, CLK, DI, ORG):
            self.pinproxy.set_as_output(pin)
            self.pinproxy.reset_pin(pin)

    def _adjust_46cmd(self, cmd):
        if self.model == 46:
            cmd >>= 2
        return cmd

    def cmd_read(self, address):
        cmd = self._adjust_46cmd(0b110000000000)
        cmd += address & 0x1ff
        self._pump(cmd, Tcsl, True)  # startbit + cmd + address ...

    def ewen(self):
        cmd = self._adjust_46cmd(0b100110000000)
        self._pump(cmd, Tcsl)

    def ewds(self):
        cmd = self._adjust_46cmd(0b100000000000)
        self._pump(cmd, Tcsl)

    def cmd_write(self, address, value):
        cmd = self._adjust_46cmd(0xa0000)
        cmd += (address << 8) + (value & 0xff)
        self._pump(cmd, Twc)

#    def wral(self, value):
#        self._pump(0x88000 + (value & 0xff), Twl)

    def eral(self):
        cmd = self._adjust_46cmd(0b100100000000)
        self._pump(cmd, Tec)

#    def cmd_erase(self, address):
#        self._pump(0xa00 + (address & 0x1ff), Twc)

    def _pump(self, command, wait_after_time=0.0, need_to_read=False):
        p = self.pinproxy
        cmdbitmask = 2 ** (command.bit_length() - 1)  # highest bit

        p.set_pin(CS)
        p.wait(Tcss)

        while cmdbitmask:
            p.set_pin(DI, command & cmdbitmask)
            cmdbitmask >>= 1
            p.wait(Tdis)
            p.set_pin(CLK)
            p.wait(Tckh)
            p.reset_pin(CLK)
            p.wait(Tckl)

        if need_to_read:
            for _ in range(8):
                p.set_pin(CLK)
                p.wait(max(Tckh, Tpd))
                p.fetch_pin(DO)
                p.reset_pin(CLK)
                p.wait(Tckl)

        p.wait(Tcsh)
        p.reset_pin(CS)
        p.wait(wait_after_time)


@TargetOp
def read(pinproxy, progressbar, model=66):
    return Ee93lcx6(pinproxy, progressbar, model).read()


@TargetOp
def write(pinproxy, progressbar, mem, model=66):
    return Ee93lcx6(pinproxy, progressbar, model).write(mem)


@TargetOp
def erase(pinproxy, progressbar, model=66):
    return Ee93lcx6(pinproxy, progressbar, model).erase()
