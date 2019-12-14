from abc import ABC, abstractmethod


# Class
class BaseServer(ABC):
    # Methods
    @abstractmethod
    async def start(self):
        raise NotImplementedError

    @abstractmethod
    async def stop(self):
        raise NotImplementedError

    # Property
    @property
    @abstractmethod
    def started(self) -> bool:
        raise NotImplementedError
