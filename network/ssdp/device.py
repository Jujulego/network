import aiohttp
import asyncio
import logging

from enum import Enum, auto
from network.device import RemoteDevice
from network.http.capability import HTTPCapability
from network.utils.xml import strip_ns
from typing import Optional, Dict, Set
from xml.etree import ElementTree as ET

from .message import SSDPMessage
from .service import SSDPService
from .urn import URN

# Constants
XML_DEVICE_NS = {
    'upnp': 'urn:schemas-upnp-org:device-1-0'
}


# Utils
def is_activation_msg(msg: SSDPMessage) -> bool:
    return msg.is_response or (msg.method == 'NOTIFY' and msg.nts == 'ssdp:alive')


# States
class DState(Enum):
    ACTIVE = auto()
    INACTIVE = auto()


# Class
class SSDPRemoteDevice(RemoteDevice, HTTPCapability):
    def __init__(self, msg: SSDPMessage, addr: str, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        RemoteDevice.__init__(self, addr, DState.INACTIVE, loop=loop)
        HTTPCapability.__init__(self, loop=loop)

        # Attributes
        # - metadata
        self.friendly_name = None  # type: Optional[str]
        self.location = msg.location
        self.root = False
        self.urns = set()  # type: Set[URN]
        self.uuid = msg.usn.uuid

        self.metadata = {}     # type: Dict[str,str]
        self.services = set()  # type: Set[SSDPService]

        # - internals
        self._logger = logging.getLogger(f'ssdp:{self.uuid}')
        self.__description_task = None   # type: Optional[asyncio.Task]
        self.__inactivate_handle = None  # type: Optional[asyncio.TimerHandle]

        # Callbacks
        self.on(DState.ACTIVE, self.on_activate)
        self.on(DState.INACTIVE, self.on_inactivate)

    # Methods
    def _activate(self, age: int):
        self.state = DState.ACTIVE

        if self.__inactivate_handle is not None:
            self.__inactivate_handle.cancel()

        self.__inactivate_handle = self._loop.call_later(age, self._inactivate)

    def _inactivate(self):
        self.state = DState.INACTIVE

        if self.__inactivate_handle is not None:
            self.__inactivate_handle.cancel()
            self.__inactivate_handle = None

        if self.__description_task is not None:
            self.__description_task.cancel()

    async def _get_description(self) -> ET.Element:
        async with self.http_get(self.location) as response:
            assert response.status == 200, f'Unable to get description (status {response.status})'
            data = await response.read()

            return ET.fromstring(data.decode('utf-8'))

    async def _parse_description(self):
        self._logger.info('Getting description')

        try:
            xml = await self._get_description()
            xml_device = xml.find('upnp:device', XML_DEVICE_NS)

            if xml_device is not None:
                # Parse xml
                for child in xml_device:
                    tag = strip_ns(child.tag)

                    if tag == 'friendlyName':
                        self.friendly_name = child.text.strip()
                    elif tag == 'serviceList':
                        self.services.add(SSDPService(child, loop=self._loop))
                    elif tag in ('iconList', 'deviceList'):
                        pass
                    else:
                        self.metadata[tag] = child.text.strip()

                # Refresh services
                for service in self.services:
                    service.up()

                self.emit('ready', self)
                self._logger.info('Ready !')
            else:
                self._logger.warning('Invalid description no device element')

        except aiohttp.ClientError as err:
            self._logger.error(f'Error while getting description: {err}')

        except AssertionError as err:
            self._logger.error(str(err))

    # Callbacks
    def on_activate(self, was: DState):
        if was == DState.INACTIVE:
            if self.__description_task is None or self.__description_task.done():
                self.__description_task = self._loop.create_task(self._parse_description())

    def on_inactivate(self, was: DState):
        for service in self.services:
            service.down()

    def on_message(self, msg: SSDPMessage):
        if msg.is_response:
            self._activate(msg.max_age or 900)

        elif msg.method == 'NOTIFY':
            if msg.nts == 'ssdp:alive':
                self._activate(msg.max_age or 900)

            elif msg.nts == 'ssdp:byebye':
                self._inactivate()

        if msg.is_response or msg.method == 'NOTIFY':
            if msg.usn.urn is not None:
                self.urns.add(msg.usn.urn)

            if msg.usn.is_root:
                self.root = True

    # Property
    @property
    def name(self) -> str:
        return self.friendly_name or self.uuid
