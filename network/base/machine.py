from abc import ABC
from typing import Generic, TypeVar

from .emitter import EventEmitter

# Types
S = TypeVar('S')


# Class
class StateMachine(Generic[S], ABC, EventEmitter):
    def __init__(self, initial: S):
        super().__init__()
        self.__state = initial

    # Methods
    def _set_state(self, s: S, *args, **kwargs):
        if s != self.__state:
            ps = self.__state
            self.__state = s

            self.emit(s, *args, was=ps, **kwargs)

    # Properties
    @property
    def state(self) -> S:
        return self.__state

    @state.setter
    def state(self, s: S):
        self._set_state(s)
