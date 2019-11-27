from abc import ABC


class RemoteDevice(ABC):
    def __init__(self, addr: str):
        self.address = addr

    def __repr__(self):
        return f'<{self.__class__.__name__}: {self.name}>'

    # Properties
    @property
    def name(self):
        return self.address
