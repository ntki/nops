import sys
import time

import lib.interfaces


REFRESH_PERIOD = 0.1


def format_output(seconds, ratio):
    assert 0 <= seconds
    assert 0 <= ratio <= 1

    plusses = "+" * int(ratio * 100 // 5)
    output = f"\r{ratio * 100:5.1f}% [{plusses: <20}] {seconds:7.3f}s"
    if ratio >= 1:
        output += '\n'
    return output


class ProgressBar(lib.interfaces.ProgressIndicator):
    def __init__(self, muted=False, output_stream=sys.stderr):
        self._muted = muted
        self._output_stream = output_stream
        self._start_ts = time.monotonic()
        self._next_show_ts = 0

    def update(self, numerator, denominator=1):
        ratio = numerator / denominator
        assert 0 <= ratio <= 1, "ratio must be in [0, 1]"
        if self._muted:
            return

        ts = time.monotonic()
        if ratio < 1 and ts < self._next_show_ts:
            return

        self._next_show_ts = ts + REFRESH_PERIOD
        elapsed = ts - self._start_ts
        if ratio >= 1:
            self._muted = True
            seconds = elapsed
        else:
            seconds = (1.0 - ratio) * elapsed / max(ratio, 1e-3)

        self._output_stream.write(format_output(seconds, ratio))
        self._output_stream.flush()
