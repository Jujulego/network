from abc import ABC


class RemoteDevice(ABC):
    def __init__(self, addr: str):
        self.address = addr
