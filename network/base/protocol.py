from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from .emitter import EventEmitter

# Type vars
T = TypeVar('T')


# Classes
class BaseProtocol(Generic[T], ABC, EventEmitter):
    # Methods
    @abstractmethod
    async def send(self, request: T):
        raise NotImplementedError

    @abstractmethod
    async def close(self):
        raise NotImplementedError
