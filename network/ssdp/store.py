import asyncio
import logging
import pyee

from network.typing import Address
from typing import Dict, Iterator, Optional, Union

from .device import SSDPRemoteDevice
from .message import SSDPMessage
from .urn import URN

# Logging
logger = logging.getLogger("ssdp")


# Class
class SSDPStore(pyee.AsyncIOEventEmitter):
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        super().__init__(loop=loop)

        # - stores
        self._devices = {}  # type: Dict[str, SSDPRemoteDevice]

    def __iter__(self):
        return iter(self._devices.values())

    def __len__(self):
        return len(self._devices)

    def __getitem__(self, uuid) -> SSDPRemoteDevice:
        return self._devices[uuid]

    # Methods
    def get(self, uuid: str) -> Optional[SSDPRemoteDevice]:
        return self._devices.get(uuid)

    def ip_filter(self, val: str) -> Iterator[SSDPRemoteDevice]:
        return filter(lambda d: val == d.address[0],  self._devices.values())

    def urn_filter(self, val: Union[str, URN]) -> Iterator[SSDPRemoteDevice]:
        if isinstance(val, str):
            val = URN(val)

        return filter(lambda d: val in d.urns, self._devices.values())

    def roots(self) -> Iterator[SSDPRemoteDevice]:
        return filter(lambda d: d.root, self._devices.values())

    # Callbacks
    def on_adv_message(self, msg: SSDPMessage, addr: Address):
        uuid = msg.usn.uuid

        if uuid not in self._devices:
            device = SSDPRemoteDevice(msg, addr, loop=self._loop)
            self._devices[uuid] = device

            self.emit('new device', device)
            logger.info(f'New device on {addr[0]}: {uuid}')

        else:
            self._devices[uuid].message(msg)
