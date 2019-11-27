import asyncio

from enum import Enum, auto
from network.device import RemoteDevice
from network.http.capability import HTTPCapability
from typing import Optional, Set
from utils.machine import StateMachine
from xml.etree import ElementTree as ET

from .message import SSDPMessage
from .urn import URN


# Utils
def is_activation_msg(msg: SSDPMessage) -> bool:
    return msg.is_response or (msg.method == 'NOTIFY' and msg.nts == 'ssdp:alive')


# States
class States(Enum):
    ACTIVE = auto
    INACTIVE = auto


# Class
class SSDPRemoteDevice(StateMachine, RemoteDevice, HTTPCapability):
    def __init__(self, msg: SSDPMessage, addr: str, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        StateMachine.__init__(self, States.INACTIVE, loop=loop)
        RemoteDevice.__init__(self, addr)
        HTTPCapability.__init__(self, loop)

        # Attributes
        # - metadata
        self.location = msg.location
        self.root = False
        self.urns = set()  # type: Set[URN]
        self.uuid = msg.usn.uuid

        # - internals
        self._inactive_handle = None  # type: Optional[asyncio.TimerHandle]

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

    async def _get_description(self, *, timeout: int = 10) -> ET.Element:
        async with self.http_get(self.location, timeout=timeout) as response:
            assert response.status == 200
            data = await response.read()

            return ET.fromstring(data.decode('utf-8'))

    def message(self, msg: SSDPMessage):
        if msg.is_response:
            self._activate(msg.max_age)

        elif msg.method == 'NOTIFY':
            if msg.nts == 'ssdp:active':
                self._activate(msg.max_age)

            elif msg.nts == 'ssdp:byebye':
                self._inactivate()

        if msg.is_response or msg.method == 'NOTIFY':
            if msg.usn.urn is not None:
                self.urns.add(msg.usn.urn)

            if msg.usn.is_root:
                self.root = True
