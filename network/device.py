import asyncio

from typing import Optional, TypeVar

from .utils.machine import StateMachine

# Types
S = TypeVar('S')


class RemoteDevice(StateMachine[S]):
    def __init__(self, addr: str, initial_state: S, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(initial_state, loop=loop)

        self.address = addr

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.name} ({self.state})>'

    # Properties
    @property
    def name(self) -> str:
        return self.address
