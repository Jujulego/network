import asyncio
import logging
import pyee

from network.typing import Address
from typing import Dict, Iterable, Optional, Union

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

    def __repr__(self):
        return f'<SSDPStore: {len(self)} devices>'

    def __iter__(self):
        return iter(self._devices.values())

    def __len__(self):
        return len(self._devices)

    def __getitem__(self, uuid: str) -> SSDPRemoteDevice:
        return self._devices[uuid]

    # Methods
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

    def show(self):
        for dev in self:
            print(f'- {repr(dev)}')

        print(f'{len(self)} device(s)')

    # Callbacks
    def on_adv_message(self, msg: SSDPMessage, addr: Address):
        uuid = msg.usn.uuid

        if uuid not in self._devices:
            device = SSDPRemoteDevice(msg, addr[0], loop=self._loop)
            self._devices[uuid] = device

            self.emit('new', device)
            logger.info(f'New device on {addr[0]}: {uuid}')

        else:
            self._devices[uuid].on_message(msg)
