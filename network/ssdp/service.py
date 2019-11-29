import asyncio

from enum import Enum, auto
from network.http.capability import HTTPCapability
from network.utils.machine import StateMachine
from network.utils.xml import strip_ns
from typing import Optional
from xml.etree import ElementTree as ET

# Constants
XML_DEVICE_NS = {
    'upnp': 'urn:schemas-upnp-org:device-1-0'
}


# States
class SState(Enum):
    UP = auto()
    DOWN = auto()


# Class
class SSDPService(StateMachine, HTTPCapability):
    def __init__(self, xml: ET.Element, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        StateMachine.__init__(self, SState.DOWN, loop=loop)
        HTTPCapability.__init__(self, loop=loop)

        # Parse xml
        self.id = xml.find('upnp:serviceId', XML_DEVICE_NS)
        self.type = xml.find('upnp:serviceType', XML_DEVICE_NS)
        self.scdp = xml.find('upnp:SCDPURL', XML_DEVICE_NS)
        self.control = xml.find('upnp:controlURL', XML_DEVICE_NS)
        self.event_sub = xml.find('upnp:eventSubURL', XML_DEVICE_NS)

        # - internals
        self.__up_task = None  # type: Optional[asyncio.Task]

    def __repr__(self):
        return f'<SSDPService: {self.id}>'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, SSDPService):
            return self.id == other.id

        return False

    # Methodes
    def up(self):
        if self.state == SState.DOWN:
            if self.__up_task is None or self.__up_task.done():
                self.__up_task = self._loop.create_task(self._up())

    async def _up(self):
        self.state = SState.UP

    def down(self):
        if self.state == SState.UP:
            self.state = SState.DOWN

            if self.__up_task is not None:
                self.__up_task.cancel()
