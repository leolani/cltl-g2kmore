import abc
import enum
from typing import Optional, Union, List, Tuple


class ConvState(enum.Enum):
    VOID = 0
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
            ConvState.VOID: [ConvState.START],
            ConvState.START: [ConvState.QUERY],
            ConvState.QUERY: [ConvState.CONFIRM],
            ConvState.CONFIRM: [ConvState.REACHED, ConvState.QUERY],
            ConvState.REACHED: [ConvState.VOID, ConvState.START],
            ConvState.GIVEUP: [ConvState.VOID, ConvState.START]
        }


class GetToKnowMore(abc.ABC):
    """
    Abstract class representing the interface of the component.
    """
    @property
    def state(self) -> ConvState:
        raise NotImplementedError()

    @property
    def desires(self) -> List[dict]:
        raise NotImplementedError()

    @desires.setter
    def desires(self, desires: List[dict]) -> None:
        raise NotImplementedError()

    @property
    def intention(self) -> dict:
        raise NotImplementedError()

    @property
    def target(self) -> Tuple[str, str]:
        raise NotImplementedError()

    def set_target(self, target_label: str, target_type: str) -> None:
        raise NotImplementedError()

    def add_knowledge(self, capsule: dict):
        raise NotImplementedError()

    def evaluate_and_act(self) -> Optional[Union[dict, str]]:
        raise NotImplementedError()

    def get_action(self) -> Optional[Union[dict, str]]:
        raise NotImplementedError()

    def reset(self):
        raise NotImplementedError()