import asyncio

from pyee import AsyncIOEventEmitter
from typing import Optional

from .message import SSDPMessage
from .protocol import SSDPProtocol


class SSDPServer(AsyncIOEventEmitter):
    def __init__(self, multicast: str, port: int, ttl: int = 4, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop or asyncio.get_event_loop())

        # - parameters
        self.multicast = multicast
        self.port = port
        self.ttl = ttl

        # - internals
        self.__started = False
        self._transport = None  # type: Optional[asyncio.DatagramTransport]
        self._protocol = None   # type: Optional[SSDPProtocol]

    # Methods
    def _on_message(self, msg: SSDPMessage):
        self.emit('message', msg)

    def _protocol_factory(self):
        return SSDPProtocol(
            self.multicast, self.port, ttl=self.ttl,
            on_message=self._on_message
        )

    async def start(self):
        if not self.__started:
            self._transport, self._protocol = await self._loop.create_datagram_endpoint(
                self._protocol_factory,
                local_addr=('0.0.0.0', self.port),
                reuse_address=True
            )

            self.__started = True

    # Properties
    @property
    def started(self):
        return self.__started
