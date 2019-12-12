from abc import ABC, abstractmethod


# Class
class BaseSession(ABC):
    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # Methods
    @abstractmethod
    async def open(self):
        raise NotImplemented

    @abstractmethod
    async def close(self):
        raise NotImplemented
