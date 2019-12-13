from typing import TypeVar

from network.base.machine import StateMachine
from network.utils.style import style as _s

# Types
S = TypeVar('S')


class RemoteDevice(StateMachine[S]):
    def __init__(self, addr: str, initial_state: S):
        super().__init__(initial_state)
        self.address = addr

    def __repr__(self):
        return _s.blue(f'<{self.__class__.__name__}: {_s.reset}{self.name}{_s.blue} ({self.state})>')

    # Properties
    @property
    def name(self) -> str:
        return self.address
