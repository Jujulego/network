import aiohttp
import asyncio
import logging

from enum import Enum, auto
from network.device import RemoteDevice
from network.http.capability import HTTPCapability
from typing import Optional, Dict, Set
from xml.etree import ElementTree as ET

from .message import SSDPMessage
from .urn import URN


# Utils
def is_activation_msg(msg: SSDPMessage) -> bool:
    return msg.is_response or (msg.method == 'NOTIFY' and msg.nts == 'ssdp:alive')


# States
class States(Enum):
    ACTIVE = auto()
    INACTIVE = auto()


# Class
class SSDPRemoteDevice(RemoteDevice, HTTPCapability):
    def __init__(self, msg: SSDPMessage, addr: str, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        RemoteDevice.__init__(self, addr, States.INACTIVE, loop=loop)
        HTTPCapability.__init__(self, loop)

        # Attributes
        # - metadata
        self.friendly_name = None  # type: Optional[str]
        self.urns = set()  # type: Set[URN]
        self.uuid = msg.usn.uuid

        self.metadata = {}  # type: Dict[str,str]
        self.location = msg.location
        self.root = False

        # - internals
        self._logger = logging.getLogger(f'ssdp:{self.uuid}')
        self.__description_task = None   # type: Optional[asyncio.Task]
        self.__inactivate_handle = None  # type: Optional[asyncio.TimerHandle]

        # Callbacks
        self.on(States.ACTIVE, self.on_activate)

        # Message
        self.on_message(msg)

    # Methods
    def _activate(self, age: int):
        self.state = States.ACTIVE

        if self.__inactivate_handle is not None:
            self.__inactivate_handle.cancel()

        self.__inactivate_handle = self._loop.call_later(age, self._inactivate)

    def _inactivate(self):
        self.state = States.INACTIVE

        if self.__inactivate_handle is not None:
            self.__inactivate_handle.cancel()
            self.__inactivate_handle = None

        if self.__description_task is not None:
            self.__description_task.cancel()

    async def _get_description(self) -> ET.Element:
        async with self.http_get(self.location) as response:
            assert response.status == 200
            data = await response.read()

            return ET.fromstring(data.decode('utf-8'))

    async def _parse_description(self):
        self._logger.info('Getting description')

        try:
            xml = await self._get_description()

            for child in xml.find('device'):
                if child.tag == 'friendlyName':
                    self.friendly_name = child.text.strip()

                elif child.tag in ['iconList', 'serviceList', 'deviceList']:
                    pass

                else:
                    self.metadata[child.tag] = child.text.strip()

            self._logger.info('Parsed description')
        except aiohttp.ClientError as err:
            self._logger.error(f'Error while getting description: {err}')

    # Callbacks
    def on_activate(self, was: States):
        if was == States.INACTIVE:
            if self.__description_task is None or self.__description_task.done():
                self.__description_task = self._loop.create_task(self._parse_description())

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
