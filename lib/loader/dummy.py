import logging
import random
import time

from lib.interfaces import BaseLoader


class Loader(BaseLoader):
    "Dummy loader (40 pin)"

    def __init__(self):
        logging.debug("loader initiated")
        self.r = random.Random(0)

    def get_output_pins(self):
        return set(range(40))

    def get_input_pins(self):
        return set(range(40))

    def open(self):
        logging.debug("open")

    def close(self):
        logging.debug("close")

    def set_as_output(self, pin):
        logging.debug("set_as_output: %s", pin)

    def set_as_input(self, pin):
        logging.debug("set_as_input: %s", pin)

    def set_pin(self, pin, new_state):
        logging.debug("set_pin: %s=%s", pin, new_state)

    def fetch_pin(self, pin, callback):
        logging.debug("fetch_pin: %s", pin)
        callback(self.r.getrandbits(1))

    def flush(self):
        logging.debug("flush")

    def wait(self, seconds):
        time.sleep(seconds)
        logging.debug("wait: %fs", seconds)
