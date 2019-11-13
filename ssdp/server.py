import asyncio
import socket

from pyee import AsyncIOEventEmitter
from typing import Optional
from utils import Address

from .message import SSDPMessage
from .protocol import SSDPProtocol

REUSE_PORT = None
if hasattr(socket, 'SO_REUSEPORT'):
    REUSE_PORT = True


class SSDPServer(AsyncIOEventEmitter):
    def __init__(self, multicast: Address, ttl: int = 4, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop or asyncio.get_event_loop())

        # - parameters
        self.multicast = multicast
        self.ttl = ttl

        # - internals
        self.__started = False
        self._transport = None  # type: Optional[asyncio.DatagramTransport]
        self._protocol = None   # type: Optional[SSDPProtocol]

    # Methods
    def _on_message(self, msg: SSDPMessage, addr: Address):
        self.emit('message', msg, addr)

        if msg.method == 'NOTIFY':
            self.emit('notify', msg, addr)

        elif msg.method == 'M-SEARCH':
            self.emit('search', msg, addr)

        elif msg.is_response:
            self.emit('response', msg, addr)

    def _protocol_factory(self):
        return SSDPProtocol(
            self.multicast, ttl=self.ttl,
            on_message=self._on_message
        )

    async def start(self):
        if not self.__started:
            self._transport, self._protocol = await self._loop.create_datagram_endpoint(
                self._protocol_factory,
                local_addr=('0.0.0.0', self.multicast[1]),
                reuse_address=True, reuse_port=REUSE_PORT
            )

            self.__started = True

    def send(self, msg: SSDPMessage):
        assert self.__started
        self._protocol.send_message(msg)

    def search(self, st):
        msg = SSDPMessage(
            method='M-SEARCH',
            headers={
                'MAN': 'ssdp:discover',
                'ST': st
            }
        )

        self.send(msg)

    def stop(self):
        if self.__started:
            self._protocol.close()

            self._protocol = None
            self._transport = None
            self.__started = False

    # Properties
    @property
    def started(self):
        return self.__started
