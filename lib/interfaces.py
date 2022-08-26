from abc import ABC, abstractmethod
from typing import Callable, Dict, Iterator, List, Set, TextIO, TypeVar


Mem = Dict[int, int]
Pin = TypeVar("Pin", int, str)
PinState = TypeVar("PinState", bool, int)


class PinProxy(ABC):
    @abstractmethod
    def pop_fetched(self,
                    tpin: Pin,
                    n_bits: int = 8,
                    n_values: int = -1,
                    lsb: bool = False) -> List[int]:
        """
        Flushes the output buffer and retrieves incoming bits from
        the input buffer forming octets (default).

        :param tpin: target pin to select the buffer
        :type tpin: Pin
        :param n_bits: length of the ints to produce, defaults to 8
        :type n_bits: int
        :param n_values: max number of ints to produce, defaults to -1 (all)
        :type n_values: int
        :param lsb: least-significant-bit first order, defaults to False (msb)
        :type lsb: bool, optional

        :return: list of ints produced from the input bitbuffer
        :rtype: [int]

        """
        pass

    @abstractmethod
    def set_as_input(self, *tpins: Pin) -> None:
        """
        Sets up the target_pin's direction as input

        :param tpin: target pin
        :type tpin: Pin
        """
        pass

    @abstractmethod
    def set_as_output(self, *tpins: Pin) -> None:
        """
        Sets up the target_pin's direction as output

        :param tpin: target pin
        :type tpin: Pin
        """
        pass

    @abstractmethod
    def set_pin(self, tpin: Pin, new_state: PinState = True) -> None:
        """
        Sets the logical output value of the target_pin to new_state

        :param tpin: target pin
        :type tpin: Pin
        :param new_state: state to be set
        :type new_state: PinState
        """
        pass

    def reset_pin(self, tpin: Pin) -> None:
        """
        Sets the logical output value of the target_pin to low(False)

        :param tpin: target pin
        :type tpin: Pin
        """
        self.set_pin(tpin, new_state=False)

    @abstractmethod
    def fetch_pin(self, tpin: Pin) -> None:
        """
        Fetches the input target pin's current value into the input buffer
        asynchronously. So it can be later retrieved with pop_fetched().

        :param tpin: target pin
        :type tpin: Pin
        """
        pass

    @abstractmethod
    def wait(self, seconds: float) -> None:
        """
        Inserts a delay into the execution.

        :param seconds: seconds to delay the execution
        :type seconds: float
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """
        Flushes the output buffer and makes sure that the Loader device is in
        sync.
        """
        pass


class ProgressIndicator(ABC):
    @abstractmethod
    def update(self, numerator: float, denominator: float = 1) -> None:
        """
        Updates the progress indicator.

        :param numerator: float, the current state of progress
        :type numerator: the current state of progress
        :param denominator: float, the maximum state of progress
        :type denominator: the maximum state of progress
        """
        pass


class BaseFileFormat(ABC):
    @abstractmethod
    def deserialize(self, reader: TextIO) -> Mem:
        pass

    @abstractmethod
    def serialize(self, mem: Mem) -> Iterator[str]:
        pass


class BaseLoader(ABC):
    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

    @abstractmethod
    def get_output_pins(self) -> Set[Pin]:
        pass

    @abstractmethod
    def get_input_pins(self) -> Set[Pin]:
        pass

    @abstractmethod
    def set_as_output(self, pin: Pin) -> None:
        pass

    @abstractmethod
    def set_as_input(self, pin: Pin) -> None:
        pass

    @abstractmethod
    def set_pin(self, pin: Pin, new_state: PinState) -> None:
        pass

    @abstractmethod
    def fetch_pin(self, pin, callback: Callable[[PinState], None]) -> None:
        pass

    @abstractmethod
    def wait(self, seconds: float) -> None:
        pass

    @abstractmethod
    def flush(self) -> None:
        pass
