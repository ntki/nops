from lib import util
from lib.targetop import TargetOp


CS = "CS"
SCK = "SCK"
SI = "SI"
SO = "SO"
HOLD = "HOLD"
WP = "WP"

SIZE = 512
CHUNK = 64

Tcss = Tcsd = 500e-9
Tsu = 50e-9
Thd = 100e-9
Ths = 200e-9
Thi = Tlo = 475e-9
Twc = 5e-3

READ = "0000a011 aaaaaaaa"  # iiiiiiii*[0,512]
WRITE = "0000a010 aaaaaaaa"  # dddddddd*[1,16]
DATA_BYTE = "dddddddd"
# WRDI = "00000100"
WREN = "00000110"
RDSR = "00000101" + "xxxxxxxx"
# WRSR = "00000001 0000ddrr"


class Ee25lc040:
    """25LC040 SPI EEPROM
    CS SCK SI SO WP HOLD"""

    def __init__(self, pinproxy, progressbar):
        self.pinproxy = pinproxy
        self.progressbar = progressbar

    def _open(self):
        self.pinproxy.set_as_input(SO)
        for pin in (CS, SCK, SI, HOLD, WP):
            self.pinproxy.set_as_output(pin)
            self.pinproxy.reset_pin(pin)
        self.pinproxy.set_pin(HOLD)
        self.pinproxy.set_pin(WP)

    def read(self):
        self._open()
        for addr in range(0, SIZE, CHUNK):
            self.progressbar.update(addr, SIZE)
            cmd = util.cmd(READ, a=addr) + [0] * 8 * CHUNK
            self._pump(cmd, 16)
        return dict(enumerate(self.pinproxy.pop_fetched(SO)))

    def erase(self):
        self._open()
        self.write({})

    def write(self, mem):
        self._open()
        for page in range(0, SIZE, 16):
            data = [mem.get(page + address, 0xff) for address in range(16)]
            self.progressbar.update(page, SIZE)
            self._wren()
            self.rdsr()
            self._write_page(page, data)
        sr_stats = self.pinproxy.pop_fetched(SO)
        # status_register = _, _, _, _, BP1, BP0, WEL, WIP
        if not all(map(lambda sr: sr & 2, sr_stats)):
            raise Exception("Write failed.")

    def _write_page(self, address, data):
        assert 1 <= len(data) <= 16
        cmd = util.cmd(WRITE, a=address)
        for byte in data:
            cmd += util.cmd(DATA_BYTE, d=byte)
        self._pump(cmd)
        self.pinproxy.wait(Twc)

    def _wren(self):  # enable write
        self._pump(util.cmd(WREN))

#    def _wrdi(self):
#        self._pump(util.cmd(WRDI))

    def rdsr(self):  # read status register
        self._pump(util.cmd(RDSR), 8)

#    def _wrsr(self, bp1, bp0):  # write status register
#        self._pump(util.cmd(WRSR, d=bp1, r=bp0))

    def _pump(self, sequence, read_after=None):
        p = self.pinproxy
        p.reset_pin(CS)
        p.wait(Tcss)

        for i, bit in enumerate(sequence):
            p.set_pin(SI, bit)
            p.wait(Tsu)
            p.set_pin(SCK)
            p.wait(Thi)
            if read_after and i >= read_after:
                p.fetch_pin(SO)
            p.wait(Thd)
            p.reset_pin(SCK)
            p.wait(Tlo)

        p.wait(Tcsd)
        p.set_pin(CS)


@TargetOp
def read(pinproxy, progressbar):
    return Ee25lc040(pinproxy, progressbar).read()


@TargetOp
def write(pinproxy, progressbar, mem):
    return Ee25lc040(pinproxy, progressbar).write(mem)


@TargetOp
def erase(pinproxy, progressbar):
    return Ee25lc040(pinproxy, progressbar).erase()
