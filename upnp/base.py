import asyncio

from network.ssdp import SSDPServer, SSDPStore
from typing import Optional


# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4


# Class
class BaseUPnP:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        # Attributes
        self._loop = loop or asyncio.get_event_loop()
        self._searching = False

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)

        self.store = SSDPStore(loop=loop)
        self.store.connect_to(self.ssdp)

    # Methods
    async def init(self):
        await self.ssdp.start()
