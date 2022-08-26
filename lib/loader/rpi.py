import sys
from time import monotonic

try:
    import RPi.GPIO as GPIO
    from RPi.GPIO import output, input, HIGH, LOW
except ModuleNotFoundError:
    print("install module 'RPi'", file=sys.stderr)  # TODO FIXME
    raise ModuleNotFoundError("install module 'RPi'")

from lib.interfaces import BaseLoader


NON_GPIO = {1, 2, 4, 6, 9, 14, 17, 20, 25, 30, 34, 39, 27, 28}
PINS = set(range(1, 41)) - NON_GPIO
LOOP_TIME = 1e-6


class Loader(BaseLoader):
    def get_output_pins(self):
        return PINS

    def get_input_pins(self):
        return PINS

    def open(self):
        GPIO.setmode(GPIO.BOARD)

    def close(self):
        GPIO.cleanup()

    def set_as_input(self, pin):
        GPIO.setup(pin, GPIO.IN)

    def set_as_output(self, pin):
        GPIO.setup(pin, GPIO.OUT)

    def set_pin(self, pin, new_state):
        output(pin, HIGH if new_state else LOW)

    def fetch_pin(self, pin, callback):
        callback(input(pin))

    def wait(self, seconds):
        if seconds > LOOP_TIME:
            wake_ts = monotonic() + seconds
            while wake_ts > monotonic():
                pass

    def flush(self):
        pass
