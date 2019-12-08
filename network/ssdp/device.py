import asyncio
import logging

from enum import Enum
from network.device import RemoteDevice
from network.utils.xml import strip_ns
from typing import Optional, Dict, List, Set
from xml.etree import ElementTree as ET

from .message import SSDPMessage
from .service import SSDPService
from .urn import URN


# Utils
def is_activation_msg(msg: SSDPMessage) -> bool:
    return msg.is_response or (msg.method == 'NOTIFY' and msg.nts == 'ssdp:alive')


# States
class DState(Enum):
    UP = 'up'
    DOWN = 'down'


# Class
class SSDPRemoteDevice(RemoteDevice):
    def __init__(self, msg: SSDPMessage, xml: ET.Element, addr: str, *,
                 parent: Optional['SSDPRemoteDevice'] = None, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(addr, DState.UP, loop=loop)

        # Attributes
        # - metadata
        self.parent = parent
        self.location = msg.location
        self.urns = set()    # type: Set[URN]
        self.metadata = {}   # type: Dict[str,str]
        self._services = {}  # type: Dict[str,SSDPService]
        self._children = {}    # type: Dict[str,SSDPRemoteDevice]

        self._parse_xml(msg, xml)

        # - internals
        self._logger = logging.getLogger(self.uuid)
        self.__down_handle = None  # type: Optional[asyncio.TimerHandle]

        # Callbacks
        self.on(DState.DOWN, self.on_down)

        # Message
        self.__down_handle = self._loop.call_later(msg.max_age or 900, self._down)

    # Methods
    def _up(self, msg: SSDPMessage):
        self._set_state(DState.UP, msg=msg)

        if self.__down_handle is not None:
            self.__down_handle.cancel()

        self.__down_handle = self._loop.call_later(msg.max_age or 900, self._down)

    def _down(self):
        self.state = DState.DOWN

        if self.__down_handle is not None:
            self.__down_handle.cancel()
            self.__down_handle = None

    def _parse_xml(self, msg: SSDPMessage, xml: ET.Element):
        for child in xml:
            tag = strip_ns(child.tag)

            if tag == 'deviceType':
                self.type = URN(child.text.strip())

            elif tag == 'friendlyName':
                self.friendly_name = child.text.strip()

            elif tag == 'UDN':
                self.uuid = child.text.strip()[5:]

            elif tag == 'serviceList':
                for xs in child:
                    service = SSDPService(xs, self.location, loop=self._loop)
                    self._services[service.id] = service

                    service.up()

            elif tag == 'deviceList':
                for xd in child:
                    device = SSDPRemoteDevice(msg, xd, self.address, parent=self, loop=self._loop)
                    self._children[device.uuid] = device

            elif tag == 'iconList':
                pass

            elif child.text is not None:
                self.metadata[tag] = child.text.strip()

    def update(self, xml: ET.Element):
        pass

    def show_children(self, lvl: int = 0):
        for dev in self.children:
            print('  ' * lvl + f'- {repr(dev)}')
            dev.show_children(lvl + 1)

    def show(self):
        print(f'Device {self.uuid}: {self.friendly_name}')
        for n, v in self.metadata.items():
            print(f'- {n}\t: {v}')

        print()
        print('Services:')
        for s in self.services:
            print(f'- {repr(s)}')

        print()
        print('Children:')
        self.show_children()

    def child(self, uuid: str) -> 'SSDPRemoteDevice':
        return self._children[uuid]

    def service(self, sid: str) -> SSDPService:
        return self._services[sid]

    # Callbacks
    def on_down(self, *_):
        for s in self.services:
            s.down()

    def on_message(self, msg: SSDPMessage):
        if msg.is_response:
            if msg.st is not None:
                self.urns.add(msg.st)

            self._up(msg)

        elif msg.method == 'NOTIFY':
            if msg.usn.urn is not None:
                self.urns.add(msg.usn.urn)

            if msg.nts == 'ssdp:alive':
                self._up(msg)

            elif msg.nts == 'ssdp:byebye':
                self._down()

    # Property
    @property
    def children(self) -> List['SSDPRemoteDevice']:
        return list(self._children.values())

    @property
    def name(self) -> str:
        return self.friendly_name or self.uuid

    @property
    def root(self) -> bool:
        return self.parent is None

    @property
    def services(self) -> List[SSDPService]:
        return list(self._services.values())

    @property
    def udn(self) -> str:
        return f'uuid:{self.uuid}'
