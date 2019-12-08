import asyncio
import itertools
import logging
import pyee

from network.typing import Address
from typing import Dict, Iterable, Optional, Union
from weakref import WeakValueDictionary

from .device import SSDPRemoteDevice
from .message import SSDPMessage
from .server import SSDPServer
from .urn import URN
from .xml import log_xml_errors, get_device_xml

# Logging
logger = logging.getLogger("ssdp")


# Class
class SSDPStore(pyee.AsyncIOEventEmitter):
    """
    Class SSDPStore:
    Collect and manages SSDP remote devices.

    Events:
    - new (device: SSDPRemoteDevice) : each time a new device is detected
    - up (device: SSDPRemoteDevice, msg: SSDPMessage) : each time a device is activated
    - down (device: SSDPRemoteDevice) : each time a device is unactivated
    """

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        super().__init__(loop=loop)

        # - stores
        self._tasks = {}    # type: Dict[str, asyncio.Task]
        self._devices = {}  # type: Dict[str, SSDPRemoteDevice]
        self._sub_devices = WeakValueDictionary()  # type: WeakValueDictionary[str, SSDPRemoteDevice]

    def __repr__(self):
        return f'<SSDPStore: {len(self)} devices>'

    def __iter__(self):
        return itertools.chain(
            self._devices.values(),
            self._sub_devices.values()
        )

    def __len__(self):
        return len(self._devices) + len(self._sub_devices)

    def __contains__(self, uuid) -> bool:
        return uuid in self._devices or uuid in self._sub_devices

    def __getitem__(self, uuid: str) -> SSDPRemoteDevice:
        try:
            if uuid in self._devices:
                return self._devices[uuid]

            return self._sub_devices[uuid]

        except KeyError:
            raise KeyError(uuid)

    # Methods
    @log_xml_errors
    async def _add_device(self, msg: SSDPMessage, addr: Address):
        xml, uuid = await get_device_xml(msg.location, loop=self._loop)
        device = SSDPRemoteDevice(msg, xml, addr[0], loop=self._loop)
        self._devices[uuid] = device

        # Connect events
        self.connect_to(device)

        # Emit new event
        self.emit('new', device)
        logger.info(f'New root device on {device.address}: {device.uuid}')

        self._add_sub_devices(device)

    def _add_sub_devices(self, device: SSDPRemoteDevice):
        for dev in device.children:
            self._sub_devices[dev.uuid] = dev

            # Connect events
            self.connect_to(dev)

            # Emit new event
            self.emit('new', dev)
            logger.info(f'New device on {dev.address}: {dev.uuid}')

            self._add_sub_devices(dev)

    @log_xml_errors
    async def _update_device(self, msg: SSDPMessage, location: str):
        xml, uuid = await get_device_xml(location, loop=self._loop)
        device = self.get(uuid)

        if device is not None:
            logger.info(f'Update device on {device.address}: {uuid}')
            device.update(msg, xml)

    def connect_to(self, obj):
        if isinstance(obj, SSDPServer):
            obj.on('notify', self.on_adv_message)
            obj.on('response', self.on_adv_message)

        elif isinstance(obj, SSDPRemoteDevice):
            obj.on('up', lambda msg, was: self.on_up(obj, msg))
            obj.on('down', lambda was: self.on_down(obj))

    def get(self, uuid: str) -> Optional[SSDPRemoteDevice]:
        return self._devices.get(uuid) or self._sub_devices.get(uuid)

    def ip_filter(self, ip: str) -> Iterable[SSDPRemoteDevice]:
        return [d for d in self if d.address == ip]

    def urn_filter(self, urn: Union[str, URN]) -> Iterable[SSDPRemoteDevice]:
        if isinstance(urn, str):
            urn = URN(urn)

        return [d for d in self if urn in d.urns]

    def roots(self) -> Iterable[SSDPRemoteDevice]:
        return list(self._devices.values())

    def _show(self, dev: SSDPRemoteDevice, lvl: int) -> int:
        count = len(dev.children)

        for d in dev.children:
            print('  ' * lvl + f'- {repr(d)}')
            count += self._show(d, lvl + 1)

        return count

    def show(self):
        for dev in self._devices.values():
            print(f'- {repr(dev)}')
            dev.show_children(1)

        print(f'{len(self)} device(s)')

    # Callbacks
    def on_up(self, device: SSDPRemoteDevice, msg: SSDPMessage):
        self.emit('up', device, msg)

        if device.root:
            if device.location not in self._tasks or self._tasks[device.location].done():
                task = self._loop.create_task(self._update_device(msg, device.location))
                self._tasks[device.location] = task

    def on_down(self, device: SSDPRemoteDevice):
        self.emit('down', device)

    def on_adv_message(self, msg: SSDPMessage, addr: Address):
        uuid = msg.usn.uuid

        if uuid not in self:
            if msg.location not in self._tasks or self._tasks[msg.location].done():
                task = self._loop.create_task(self._add_device(msg, addr))
                self._tasks[msg.location] = task

        else:
            self[uuid].on_message(msg)
