import abc
import enum
from typing import Optional, Union


class ConvState(enum.Enum):
    START = 1
    QUERY = 2
    CONFIRM = 3
    REACHED = 4
    GIVEUP = 5

    def transitions(self):
        return self._allowed[self]

    @property
    def _allowed(self):
        return {
            ConvState.START: [ConvState.QUERY],
            ConvState.QUERY: [ConvState.CONFIRM],
            ConvState.CONFIRM: [ConvState.REACHED, ConvState.QUERY],
            ConvState.REACHED: [ConvState.START]
        }


class GetToKnowMore(abc.ABC):
    """
    Abstract class representing the interface of the component.
    """
    @property
    def state(self) -> ConvState:
        raise NotImplementedError()

    @property
    def desires(self) -> dict:
        raise NotImplementedError()

    @desires.setter
    def set_desires(self, thoughts: dict) -> None:
        raise NotImplementedError()

    @property
    def intention(self) -> dict:
        raise NotImplementedError()

    def add_knowledge(self, capsule: dict):
        raise NotImplementedError()

    def get_action(self) -> Optional[Union[dict, str]]:
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()