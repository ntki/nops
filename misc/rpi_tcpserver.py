#!/usr/bin/python3

import argparse
from itertools import zip_longest
import logging
import socket
import sys
from time import monotonic

# enum.Enum would be too slow
OP_SETPIN_LOW = 0
OP_SETPIN_HIGH = 0x20
OP_WAIT_100NS = 0x40
OP_READPIN = 0x60
OP_SET_AS_OUTPUT = 0x80
OP_SET_AS_INPUT = 0xA0
OP_FLUSH = 0xC0

FLUSH_DONE = b'\xff'
PROGRESS_CHUNKSIZE = 2 ** 10
PROGRESS_MARK = b'\x11'

logger = logging.getLogger(__name__)


def handle_client(client):
    buffer = bytearray()
    wakeup_ts = 0
    op_count = 0
    while data := client.recv(1024):
        buffer += data

        for op, arg in zip_longest(buffer[::2], buffer[1::2], fillvalue=None):
            while wakeup_ts > monotonic():
                pass
            wakeup_ts = 0

            if arg is None:  # last odd pair
                buffer = buffer[-1]
                break

            if op == OP_SETPIN_LOW:
                output(arg, LOW)
            elif op == OP_SETPIN_HIGH:
                output(arg, HIGH)
            elif op & 0xe0 == OP_WAIT_100NS:
                wakeup_ts = monotonic() + (arg + ((op & 0x1f) << 8) + 1) / 1e7
            elif op == OP_READPIN:
                client.send(input(arg).to_bytes(1, 'big'))
            elif op == OP_FLUSH:
                client.send(FLUSH_DONE)
            elif op == OP_SET_AS_OUTPUT:
                GPIO.setup(arg, GPIO.OUT)
            elif op == OP_SET_AS_INPUT:
                GPIO.setup(arg, GPIO.IN)
            else:
                logger.warning(f"Invalid opcode received: {op}")
            op_count += 1
            if op_count % PROGRESS_CHUNKSIZE == 0:
                client.send(PROGRESS_MARK)
        buffer.clear()


def serve_forever(address, port):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)
    s.bind((address, port))
    s.listen(1)

    while True:
        logger.info(f"Waiting for client on {s.getsockname()}...")
        client, raddr = s.accept()
        logger.info(f"Accepted connection: {raddr}")

        GPIO.setmode(GPIO.BOARD)
        try:
            handle_client(client)
        except (BrokenPipeError, ConnectionError) as e:
            logger.warning(f"{e}")
        logger.info("Connection closed.")
        GPIO.cleanup()


def parse_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument("-b", "--bind", default="0.0.0.0")
    p.add_argument("-p", "--port", type=int, default=30456)
    return p.parse_args(argv)


if __name__ == "__main__":
    import RPi.GPIO as GPIO
    from RPi.GPIO import output, input, HIGH, LOW

    args = parse_args(sys.argv[1:])

    logging.basicConfig(
        level=logging.DEBUG,
        datefmt="%H:%M:%S",
        format="[%(asctime)s.%(msecs)0.3d] %(message)s")
    logger.info(f"args: {sys.argv}")

    serve_forever(args.bind, args.port)
