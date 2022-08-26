from collections import defaultdict, deque
import enum
import re

from lib.interfaces import PinProxy


RE_PINMAP = r'(?P<key>\w+)' r'\s*=\s*' r'(?P<value>\w+)'
IGNORED_MARK = "_"
IGNORED = object()


class Direction(enum.Enum):
    IN = 1
    OUT = 2


def parse_pinmap(pinmap_args):
    result = {}
    if not pinmap_args:
        return result
    for m in pinmap_args:
        for k, v in re.findall(RE_PINMAP, m):
            if v.isdigit():
                v = int(v)
            elif v == IGNORED_MARK:
                v = IGNORED
            result[k] = v
    return result


class ThePinProxy(PinProxy):
    def __init__(self, loader, pinmap):
        self._loader = loader
        self._check_pinmap(pinmap)
        self._pinmap = pinmap  # target_pin: loader_pin
        self._tdirs = {}  # target_pin: direction
        self._input_buffer = defaultdict(deque)  # tpin: incoming_bits

    def pop_fetched(self, tpin, n_bits=8, n_values=-1, lsb=False):
        self.flush()
        self._get_lpin(tpin)
        bq = self._input_buffer[tpin]
        coeffs = [2 ** x for x in range(n_bits)]
        if not lsb:
            coeffs.reverse()
        result = []
        while len(bq) >= n_bits and n_values != 0:
            value = sum(bool(bq.popleft()) * c for c in coeffs)
            result.append(value)
            n_values -= 1
        return result

    def set_as_input(self, *tpins):
        for tpin in tpins:
            self._set_direction(tpin, Direction.IN)

    def set_as_output(self, *tpins):
        for tpin in tpins:
            self._set_direction(tpin, Direction.OUT)

    def set_pin(self, tpin, new_state=True):
        self._check_tpin_direction(tpin, Direction.OUT)
        lpin = self._get_lpin(tpin)
        if lpin != IGNORED:
            self._loader.set_pin(lpin, new_state)

    def fetch_pin(self, tpin):
        self._check_tpin_direction(tpin, Direction.IN)
        lpin = self._get_lpin(tpin)
        if lpin != IGNORED:
            self._loader.fetch_pin(lpin, self._input_buffer[tpin].append)

    def wait(self, seconds):
        self._loader.wait(seconds)

    def flush(self):
        self._loader.flush()

    def __enter__(self):
        self._loader.open()
        return self

    def __exit__(self, *_):
        self._loader.close()

    def _get_lpins_by_direction(self, direction: Direction):
        if direction == Direction.OUT:
            return self._loader.get_output_pins()
        return self._loader.get_input_pins()

    def _check_pinmap(self, pinmap):
        lpins = self._get_lpins_by_direction(Direction.OUT) \
            | self._get_lpins_by_direction(Direction.IN)
        if missing := set(pinmap.values()) - lpins - {IGNORED}:
            raise KeyError(f"loader pins '{missing}' are not provided")

    def _check_tpin_direction(self, tpin, direction):
        if self._tdirs.get(tpin) != direction:
            raise ValueError(f"'{tpin}' is not set as '{direction.name}'")

    def _get_lpin(self, tpin):
        try:
            return self._pinmap[tpin]
        except KeyError:
            raise KeyError(f"unassigned pin: '{tpin}'")

    def _set_direction(self, tpin, direction):
        lpin = self._get_lpin(tpin)
        if lpin != IGNORED and self._tdirs.get(tpin) != direction:
            if lpin not in self._get_lpins_by_direction(direction):
                raise ValueError(f"'{tpin}->{lpin}' cannot be set up "
                                 f"as '{direction.name}'")
            if direction == Direction.OUT:
                self._loader.set_as_output(lpin)
            else:
                self._loader.set_as_input(lpin)
        self._tdirs[tpin] = direction
