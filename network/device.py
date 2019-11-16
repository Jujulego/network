from abc import ABC

from .typing import Address


class RemoteDevice(ABC):
    def __init__(self, addr: Address):
        self.address = addr
