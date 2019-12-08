import asyncio
import pyee

from abc import ABC
from typing import Generic, Optional, TypeVar

# Types
S = TypeVar('S')


# Class
class StateMachine(Generic[S], ABC, pyee.AsyncIOEventEmitter):
    def __init__(self, initial: S, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        pyee.AsyncIOEventEmitter.__init__(self, loop=loop)
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
