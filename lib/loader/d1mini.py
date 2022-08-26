import collections
import logging
import math
import time

# TODO import hibakezeles
import serial

from lib.interfaces import BaseLoader


OP_SETPIN_HIGH = 0x00
OP_SETPIN_LOW = 0x20
OP_WAIT_US = 0x40
OP_READ = 0x60
OP_SET_AS_OUTPUT = 0x80
OP_SET_AS_INPUT = 0xA0
# D4 == 2, LED_BUILTIN, used by the bootloader
PINS = {"D0": 16, "D1": 5, "D2": 4, "D3": 0,
        "D5": 14, "D6": 12, "D7": 13, "D8": 15}
LOOP_TIME_US = 15
PROGRESS_CHUNKSIZE = 32
PROGRESS_MARK = 0x11


class Loader(BaseLoader):
    "D1 Mini driver"

    def __init__(self, device="/dev/ttyUSB0", baudrate=921600):
        self._baudrate = baudrate
        self._device = device
        self._port = None
        self._read_callbacks = collections.deque()
        self._unprocessed = 0
        self._pin_state = {k: None for k in PINS}

    def get_output_pins(self):
        return set(PINS.keys())

    def get_input_pins(self):
        return set(PINS.keys())

    def open(self):
        self._port = serial.Serial(self._device, self._baudrate)
        self._reset()

    def _reset(self):
        self._port.setDTR(False)
        self._port.setRTS(False)
        self._port.setDTR(True)
        self._port.setRTS(True)
        time.sleep(0.3)
        self._port.reset_input_buffer()
        logging.debug("Reset done")

    def close(self):
        if self._port:
            self.flush()
            self._reset()
            self._port.close()
            self._port = None

    def set_as_input(self, pin):
        self._send(OP_SET_AS_INPUT | PINS[pin])
        self._pin_state[pin] = None

    def set_as_output(self, pin):
        self._send(OP_SET_AS_OUTPUT | PINS[pin])
        self._pin_state[pin] = None

    def set_pin(self, pin, new_state=True):
        if self._pin_state[pin] != new_state:
            self._send(
                (OP_SETPIN_HIGH if new_state else OP_SETPIN_LOW) | PINS[pin])
            self._pin_state[pin] = new_state

    def fetch_pin(self, pin, callback):
        self._read_callbacks.append(callback)
        self._send(OP_READ | PINS[pin])

    def wait(self, seconds):
        usec = math.ceil(seconds * 1e6)
        while usec > LOOP_TIME_US:
            usec -= LOOP_TIME_US
            n = min(usec, 31)
            usec -= n
            self._send(OP_WAIT_US | n)

    def flush(self):
        self.fetch_pin("D0", lambda _: 0)
        self._port.flush()
        self._handle_read()

    def _send(self, cmd):
        self._unprocessed += self._port.write([cmd])
        if self._unprocessed % PROGRESS_CHUNKSIZE == 0:
            self._read_callbacks.append(self._progress_mark_received)
        while self._unprocessed >= PROGRESS_CHUNKSIZE * 8:
            self._handle_read(1)

    def _progress_mark_received(self, x):
        assert x == PROGRESS_MARK
        self._unprocessed -= PROGRESS_CHUNKSIZE

    def _handle_read(self, n=None):
        n = n or len(self._read_callbacks)
        for b in self._port.read(n):
            self._read_callbacks.popleft()(b)
