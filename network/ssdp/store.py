import aiohttp
import asyncio
import logging
import pyee

from network.typing import Address
from typing import Dict, Iterable, Optional, Union
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
        self._tasks = {}    # type: Dict[str, asyncio.Task]

    def __repr__(self):
        return f'<SSDPStore: {len(self)} devices>'

    def __iter__(self):
        return iter(self._devices.values())

    def __len__(self):
        return len(self._devices)

    def __getitem__(self, uuid: str) -> SSDPRemoteDevice:
        return self._devices[uuid]

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
                logger.info(f'New root device on {addr[0]}: {device.uuid}')

        except aiohttp.ClientError as err:
            logger.error(f'Error while getting description: {err}')

        except AssertionError as err:
            logger.error(f'Error while getting description: {err}')

        except Exception:
            logger.exception(f'Error while parsing description ({msg.location})')

    def connect_to(self, srv: SSDPServer):
        srv.on('notify', self.on_adv_message)
        srv.on('response', self.on_adv_message)

    def get(self, uuid: str) -> Optional[SSDPRemoteDevice]:
        return self._devices.get(uuid)

    def ip_filter(self, ip: str) -> Iterable[SSDPRemoteDevice]:
        return [d for d in self if d.address == ip]

    def urn_filter(self, urn: Union[str, URN]) -> Iterable[SSDPRemoteDevice]:
        if isinstance(urn, str):
            urn = URN(urn)

        return [d for d in self if urn in d.urns]

    def roots(self) -> Iterable[SSDPRemoteDevice]:
        return [d for d in self if d.root]

    def _show(self, dev: SSDPRemoteDevice, lvl: int) -> int:
        count = len(dev.children)

        for d in dev.children:
            print('  ' * lvl + f'- {repr(d)}')
            count += self._show(d, lvl + 1)

        return count

    def show(self):
        count = len(self)

        for dev in self:
            print(f'- {repr(dev)}')
            count += self._show(dev, 1)

        print(f'{count} device(s)')

    # Callbacks
    def on_adv_message(self, msg: SSDPMessage, addr: Address):
        uuid = msg.usn.uuid

        if uuid not in self._devices:
            if msg.location not in self._tasks or self._tasks[msg.location].done():
                task = self._loop.create_task(self._get_description(msg, addr))
                self._tasks[msg.location] = task

        else:
            self._devices[uuid].on_message(msg)
