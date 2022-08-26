import collections
import math
import socket

from lib.interfaces import BaseLoader
import misc.rpi_tcpserver as RT


NON_GPIO = {1, 2, 4, 6, 9, 14, 17, 20, 25, 27, 28, 30, 34, 39}
PINS = set(range(1, 41)) - NON_GPIO
LOOP_TIME_100NS = 10


class Loader(BaseLoader):
    def __init__(self, host='localhost', port=30456):
        self._remote_address = (host, port)
        self._read_callbacks = collections.deque()
        self._s = socket.socket()
        self._pin_state = {k: None for k in PINS}
        self._unprocessed = 0

    def open(self):
        self._s.connect(self._remote_address)

    def close(self):
        self.flush()
        self._s.close()

    def get_output_pins(self):
        return PINS

    def get_input_pins(self):
        return PINS

    def set_as_input(self, pin):
        self._send(RT.OP_SET_AS_INPUT, pin)
        self._pin_state[pin] = None

    def set_as_output(self, pin):
        self._send(RT.OP_SET_AS_OUTPUT, pin)
        self._pin_state[pin] = None

    def set_pin(self, pin, new_state):
        if self._pin_state[pin] != new_state:
            self._send(
                RT.OP_SETPIN_HIGH if new_state else RT.OP_SETPIN_LOW,
                pin)
            self._pin_state[pin] = new_state

    def fetch_pin(self, pin, callback):
        self._read_callbacks.append(callback)
        self._send(RT.OP_READPIN, pin)

    def wait(self, seconds):
        ns100 = math.ceil(seconds * 1e7)
        while ns100 > LOOP_TIME_100NS:
            n = min(ns100, 2**13)
            ns100 -= n
            n -= 1
            self._send(RT.OP_WAIT_100NS | (n >> 8), n & 0xff)

    def flush(self):
        self._read_callbacks.append(lambda _: 0)
        self._send(RT.OP_FLUSH, 0)
        self._handle_recv(block=True)

    def _progress_mark_received(self, x):
        assert x == int.from_bytes(RT.PROGRESS_MARK, 'big')
        self._unprocessed -= RT.PROGRESS_CHUNKSIZE

    def _send(self, cmd, arg):
        self._s.send(bytes([cmd, arg]))  # TODO handle exception
        self._unprocessed += 1
        if self._unprocessed % RT.PROGRESS_CHUNKSIZE == 0:
            self._read_callbacks.append(self._progress_mark_received)
        if self._unprocessed >= RT.PROGRESS_CHUNKSIZE * 8 \
                or len(self._read_callbacks) >= 512:
            self._handle_recv()

    def _handle_recv(self, block=False):
        while self._read_callbacks:
            if not (resp := self._s.recv(512)):
                raise Exception("Connection lost.")  # TODO
            for b in resp:
                self._read_callbacks.popleft()(b)
            if not block:
                return
