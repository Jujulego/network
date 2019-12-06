import aiohttp
import asyncio
import itertools
import logging
import pyee

from network.typing import Address
from typing import Dict, Iterable, Optional, Union
from weakref import WeakValueDictionary
from xml.etree import ElementTree as ET

from .constants import XML_DEVICE_NS
from .device import SSDPRemoteDevice
from .message import SSDPMessage
from .server import SSDPServer
from .urn import URN

# Logging
logger = logging.getLogger("ssdp")


# Class
class SSDPStore(pyee.AsyncIOEventEmitter):
    """
    Class SSDPStore:
    Collect and manages SSDP devices.

    Events:
    - new (device: SSDPDevice) : each time a new device is detected
    """

    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        super().__init__(loop=loop)

        # - stores
        self._devices = {}  # type: Dict[str, SSDPRemoteDevice]
        self._sub_devices = WeakValueDictionary()  # type: WeakValueDictionary[str, SSDPRemoteDevice]
        self._tasks = {}    # type: Dict[str, asyncio.Task]

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
    async def _get_description(self, msg: SSDPMessage, addr: Address):
        # noinspection PyBroadException
        try:
            # Get xml description
            logger.info(f'Getting description of {msg.usn.uuid}')

            async with aiohttp.ClientSession(loop=self._loop) as session:
                async with session.get(msg.location) as response:
                    assert response.status == 200, f'Unable to get description (status {response.status})'
                    data = await response.read()

                    xml = ET.fromstring(data)

            # Parse it !
            device = xml.find('upnp:device', XML_DEVICE_NS)

            if device is None:
                logger.warning(f'Invalid description: no device element ({msg.location})')
            else:
                device = SSDPRemoteDevice(msg, device, addr[0], loop=self._loop)
                self._devices[device.uuid] = device

                self.emit('new', device)
                logger.info(f'New root device on {device.address}: {device.uuid}')

                self._add_sub_devices(device)

        except aiohttp.ClientError as err:
            logger.error(f'Error while getting description: {err}')

        except AssertionError as err:
            logger.error(f'Error while getting description: {err}')

        except Exception:
            logger.exception(f'Error while parsing description ({msg.location})')

    def _add_sub_devices(self, device: SSDPRemoteDevice):
        for dev in device.children:
            self._sub_devices[dev.uuid] = dev

            self.emit('new', dev)
            logger.info(f'New device on {dev.address}: {dev.uuid}')

            self._add_sub_devices(dev)

    def connect_to(self, srv: SSDPServer):
        srv.on('notify', self.on_adv_message)
        srv.on('response', self.on_adv_message)

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
        count = len(self._devices)

        for dev in self._devices.values():
            print(f'- {repr(dev)}')
            count += self._show(dev, 1)

        print(f'{count} device(s)')

    # Callbacks
    def on_adv_message(self, msg: SSDPMessage, addr: Address):
        uuid = msg.usn.uuid

        if uuid not in self:
            if msg.location not in self._tasks or self._tasks[msg.location].done():
                task = self._loop.create_task(self._get_description(msg, addr))
                self._tasks[msg.location] = task

        else:
            self[uuid].on_message(msg)
