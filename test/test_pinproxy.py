import unittest.mock

import pytest

from lib.interfaces import BaseLoader
from lib.pinproxy import IGNORED, ThePinProxy


PINMAP = {"I1": 0, "I2": 1,
          "O1": 2, "O2": 3,
          "IO1": 6, "IO2": 7,
          "X": IGNORED}


@pytest.fixture
def pinproxy():
    mock_loader = unittest.mock.create_autospec(BaseLoader)
    mock_loader.get_output_pins.return_value = {2, 3, 6, 7}
    mock_loader.get_input_pins.return_value = {0, 1, 6, 7}

    pinproxy = ThePinProxy(mock_loader, PINMAP)
    mock_loader.get_output_pins.assert_called_once()
    mock_loader.get_input_pins.assert_called_once()
    yield pinproxy


def test_fail_on_missing_lpins():
    mock_loader = unittest.mock.create_autospec(BaseLoader)
    mock_loader.get_output_pins.return_value = {2, 3}
    mock_loader.get_input_pins.return_value = {0, 1}

    with pytest.raises(KeyError):
        ThePinProxy(mock_loader, PINMAP)


def test_setting_correct_directions(pinproxy):
    for pin in ("I1", "I2", "IO1", "IO2", "X"):
        pinproxy.set_as_input(pin)
    for pin in ("O1", "O2", "IO1", "IO2", "X"):
        pinproxy.set_as_output(pin)


def test_unassigned_pin_fails(pinproxy):
    with pytest.raises(Exception):
        pinproxy.set_as_input("unassigned")


def test_direction_mismatch_fails(pinproxy):
    with pytest.raises(ValueError):
        pinproxy.set_as_output("I1")
    with pytest.raises(ValueError):
        pinproxy.set_as_input("O1")


def test_set_pin(pinproxy):
    pinproxy.set_as_output("O1")
    pinproxy.set_pin("O1", True)
    pinproxy._loader.set_pin.assert_called_with(2, True)
    pinproxy.reset_pin("O1")
    pinproxy._loader.set_pin.assert_called_with(2, False)


def test_set_pin_fails_on_direction_mismatch(pinproxy):
    pinproxy.set_as_input("I1")
    with pytest.raises(ValueError):
        pinproxy.set_pin("I1", True)


def test_set_pin_fails_on_unassigned_pin(pinproxy):
    with pytest.raises(ValueError):
        pinproxy.set_pin("unassigned", True)


def test_set_pin_noop_on_ignored_pin(pinproxy):
    pinproxy.set_as_output("X")
    pinproxy.set_pin("X", True)
    pinproxy._loader.set_pin.assert_not_called()


def test_fetch_pin(pinproxy):
    pinproxy.set_as_input("I1")
    pinproxy.fetch_pin("I1")
    pinproxy._loader.fetch_pin.assert_called_once()


def test_fetch_pin_fails_on_direction_mismatch(pinproxy):
    pinproxy.set_as_output("O1")
    with pytest.raises(ValueError):
        pinproxy.fetch_pin("O1")
    with pytest.raises(ValueError):
        pinproxy.fetch_pin("O2")


def test_wait(pinproxy):
    pinproxy.wait(456.678)
    pinproxy._loader.wait.assert_called_with(456.678)


def test_flush(pinproxy):
    pinproxy.flush()
    pinproxy._loader.flush.assert_called_once()


def test_pop_fetched_bits(pinproxy):
    pinproxy._input_buffer["I1"] = []
    assert pinproxy.pop_fetched("I1") == []
    pinproxy._loader.flush.assert_called_once()


def test_pop_fetched_octets_lsb(pinproxy):
    pinproxy._input_buffer["I1"].extend([1, 0] * 4 + [0, 1] * 4)
    assert pinproxy.pop_fetched("I1", lsb=True) == [0x55, 0xaa]


def test_pop_fetched_octets_and_rest(pinproxy):
    pinproxy._input_buffer["I1"].extend([1, 0] * 4 + [0, 1] * 4 + [1, 1])
    assert pinproxy.pop_fetched("I1") == [0xaa, 0x55]
    assert pinproxy.pop_fetched("I1") == []
    assert pinproxy.pop_fetched("I1", 2) == [0x3]


def test_pop_fetched_words(pinproxy):
    pinproxy._input_buffer["I1"].extend([1, 0] * 4 + [0, 1] * 4)
    assert pinproxy.pop_fetched("I1", 16) == [0xaa55]


def test_pop_fetched_max(pinproxy):
    pinproxy._input_buffer["I1"].extend([1, 0] * 4 + [0, 1] * 4 + [1, 1])
    assert pinproxy.pop_fetched("I1", 2, n_values=2) == [2, 2]
    assert pinproxy.pop_fetched("I1", 3, n_values=1) == [5]
