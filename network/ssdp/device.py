import asyncio
import logging

from network.base.device import RemoteDevice
from network.utils.xml import strip_ns
from typing import Optional, Dict, List, Set
from xml.etree import ElementTree as ET

from .message import SSDPMessage
from .service import SSDPService
from .urn import URN
from .xml import log_xml_errors, get_device_uuid, get_service_xml, get_service_id


# Utils
def is_activation_msg(msg: SSDPMessage) -> bool:
    return msg.is_response or (msg.method == 'NOTIFY' and msg.nts == 'ssdp:alive')


# Class
class SSDPRemoteDevice(RemoteDevice):
    """
    class SSDPRemoteDevice:
    Represent and interacts with a SSDP remote device

    Events:
    - up (was: str)              : each time the device goes to the state 'up' (was is the previous state)
    - new (service: SSDPService) : each time a new service is added
    - down (was: str)            : each time the device goes to the state 'down' (was is the previous state)
    """

    def __init__(self, msg: SSDPMessage, xml: ET.Element, addr: str, parent: Optional['SSDPRemoteDevice'] = None):
        super().__init__(addr, 'down')

        # Attributes
        # - metadata
        self.parent = parent
        self.location = msg.location
        self.uuid = get_device_uuid(xml, self.location)
        self.urns = set()    # type: Set[URN]
        self.metadata = {}   # type: Dict[str,str]
        self._services = {}  # type: Dict[str,SSDPService]
        self._children = {}  # type: Dict[str,SSDPRemoteDevice]

        # - internals
        self._loop = asyncio.get_event_loop()
        self._logger = logging.getLogger(self.uuid)
        self._tasks = {}           # type: Dict[str, asyncio.Task]
        self.__down_handle = None  # type: Optional[asyncio.TimerHandle]

        # Parse xml
        self._parse_xml(msg, xml)

        # Callbacks
        self.on('down', self.on_down)

        # Message
        self.on_message(msg)

    # Methods
    def _up(self, msg: SSDPMessage):
        self._set_state('up', msg=msg)

        if self.__down_handle is not None:
            self.__down_handle.cancel()

        self.__down_handle = self._loop.call_later(msg.max_age or 900, self._down)

    def _down(self):
        self.state = 'down'

        if self.__down_handle is not None:
            self.__down_handle.cancel()
            self.__down_handle = None

    def _parse_xml(self, msg: SSDPMessage, xml: ET.Element):
        # Extract services, sub-devices and metadata
        for child in xml:
            tag = strip_ns(child.tag)

            if tag == 'deviceType':
                self.type = URN(child.text.strip())

            elif tag == 'friendlyName':
                self.friendly_name = child.text.strip()

            elif tag == 'UDN':
                pass
            elif tag == 'serviceList':
                for xs in child:
                    sid = get_service_id(xs, self.location)

                    if sid not in self._tasks or self._tasks[sid].done():
                        task = self._loop.create_task(self._update_service(xs))
                        self._tasks[sid] = task

            elif tag == 'deviceList':
                for xd in child:
                    self._update_sub_device(xd, msg)

            elif tag == 'iconList':
                pass

            elif child.text is not None:
                self.metadata[tag] = child.text.strip()

    @log_xml_errors
    async def _update_service(self, xmld: ET.Element):
        xmls, sid = await get_service_xml(xmld, self.location)
        service = self._services.get(sid)

        if service is not None:
            self._logger.info(f'Update service: {sid}')
            service.update(xmld, xmls, self.location)

        else:
            self._logger.info(f'New service: {sid}')
            service = SSDPService(xmld, xmls, self.location)
            self._services[sid] = service

            # Emit new event
            self.emit('new', service)

    def _update_sub_device(self, xml: ET.Element, msg: SSDPMessage):
        uuid = get_device_uuid(xml, self.location)
        device = self._children.get(uuid)

        if device is not None:
            device.update(msg, xml)

        else:
            device = SSDPRemoteDevice(msg, xml, self.address, parent=self)
            self._children[uuid] = device

    def update(self, msg: SSDPMessage, xml: ET.Element):
        self._logger.info('Updating')

        # Resets
        self.metadata = {}
        self.location = msg.location

        # Parse
        self._parse_xml(msg, xml)

    def show_children(self, lvl: int = 0):
        for dev in self.children:
            print('  ' * lvl + f'- {repr(dev)}')
            dev.show_children(lvl + 1)

    def show(self):
        print(f'Device {self.uuid}: {self.friendly_name}')
        for n, v in self.metadata.items():
            print(f'- {n}:\t{v}')

        if len(self.services) > 0:
            print()
            print('Services:')
            for s in self.services:
                print(f'- {repr(s)}')

        if len(self.children) > 0:
            print()
            print('Children:')
            self.show_children()

    def child(self, uuid: str) -> 'SSDPRemoteDevice':
        return self._children[uuid]

    def service(self, sid: str) -> SSDPService:
        return self._services[sid]

    # Callbacks
    def on_down(self, was: str):
        for task in self._tasks.values():
            task.cancel()

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
