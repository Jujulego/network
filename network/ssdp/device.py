import asyncio

from enum import Enum, auto
from network.device import RemoteDevice
from network.typing import Address
from typing import Optional
from utils.machine import StateMachine

from .message import SSDPMessage


# Utils
def is_activation_msg(msg: SSDPMessage) -> bool:
    return msg.is_response or (msg.method == 'NOTIFY' and msg.nts == 'ssdp:alive')


# States
class States(Enum):
    ACTIVE = auto
    INACTIVE = auto


# Class
class SSDPRemoteDevice(StateMachine, RemoteDevice):
    def __init__(self, msg: SSDPMessage, addr: Address, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        StateMachine.__init__(self, States.INACTIVE, loop=loop)
        RemoteDevice.__init__(self, addr)

        # Attributes
        # - metadata
        self.uuid = msg.usn.uuid

        # - internals
        self._inactivate_handle = None  # type: Optional[asyncio.TimerHandle]

        # Message
        self.message(msg)

    def __repr__(self):
        return f'<SSDPRemoteDevice: {self.uuid} ({self.state})>'

    # Methods
    def _activate(self, age: int):
        self.state = States.ACTIVE

        if self._inactive_handle is not None:
            self._inactive_handle.cancel()

        self._inactive_handle = self._loop.call_later(age, self._inactivate)

    def _inactivate(self):
        self.state = States.INACTIVE

        if self._inactive_handle is not None:
            self._inactive_handle.cancel()
            self._inactive_handle = None

    def message(self, msg: SSDPMessage):
        if msg.is_response:
            self._activate(msg.max_age)

        elif msg.method == 'NOTIFY':
            if msg.nts == 'ssdp:active':
                self._activate(msg.max_age)

            elif msg.nts == 'ssdp:byebye':
                self._inactivate()
