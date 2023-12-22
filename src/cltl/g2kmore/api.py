import abc
from typing import Optional, Tuple, Iterable

class GetToKnowMore(abc.ABC):
    """
    Abstract class representing the interface of the component.
    """
    def utterance_detected(self, utterance: str) -> Optional[str]:
        raise NotImplementedError()

    def response(self) -> Optional[str]:
        raise NotImplementedError()

    @property
    def speaker(self) -> Tuple[str, str]:
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()