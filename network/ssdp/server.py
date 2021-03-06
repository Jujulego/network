import asyncio
import socket
import sys

from network.base.emitter import EventEmitter
from network.base.protocol import BaseProtocol
from network.base.server import BaseServer
from network.typing import Address
from typing import Optional, Type

from .message import SSDPMessage
from .protocol import SSDPProtocol, SSDPSearchProtocol
from .windows import WindowsSearchProtocol

# Constants
ON_WINDOWS = sys.platform == 'win32'
REUSE_PORT = True if hasattr(socket, 'SO_REUSEPORT') else None


# Class
class SSDPServer(BaseServer, EventEmitter):
    def __init__(self, multicast: Address, ttl: int = 4):
        super().__init__()

        # - parameters
        self.multicast = multicast
        self.ttl = ttl

        # - internals
        self.__started = False
        self._loop = asyncio.get_event_loop()
        self._transport = None  # type: Optional[asyncio.DatagramTransport]
        self._protocol = None   # type: Optional[SSDPProtocol]

    # Methods
    def _on_message(self, msg: SSDPMessage, addr: Address):
        self.emit('message', msg, addr)

        if msg.is_response:
            self.emit('response', msg, addr)

        elif msg.method == 'NOTIFY':
            self.emit('notify', msg, addr)

        elif msg.method == 'M-SEARCH':
            self.emit('search', msg, addr)

    def _protocol_factory(self, protocol: Type[SSDPProtocol] = SSDPProtocol):
        return lambda: protocol(
            self.multicast, ttl=self.ttl
        )

    async def start(self):
        if not self.__started:
            self._transport, self._protocol = await self._loop.create_datagram_endpoint(
                self._protocol_factory(),
                local_addr=('0.0.0.0', self.multicast[1]),
                reuse_address=True, reuse_port=REUSE_PORT,
                allow_broadcast=True
            )

            self._protocol.on('recv', self._on_message)
            self.__started = True

    def send(self, msg: SSDPMessage):
        assert self.__started
        self._protocol.send(msg)

    async def search(self, *targets: str, mx: int = 5) -> BaseProtocol[SSDPMessage]:
        # Prepare protocol
        if ON_WINDOWS:
            protocol = WindowsSearchProtocol(self.multicast, ttl=self.ttl)

        else:
            _, protocol = await self._loop.create_datagram_endpoint(
                self._protocol_factory(SSDPSearchProtocol),
                family=socket.AF_INET,
                allow_broadcast=True
            )

        protocol.on('recv', self._on_message)

        # Send message
        for st in targets:
            msg = SSDPMessage(
                method='M-SEARCH',
                headers={
                    'HOST': '239.255.255.250:1900',
                    'MAN': '"ssdp:discover"',
                    'MX': mx,
                    'ST': st
                }
            )

            await protocol.send(msg)

        async def close():
            await asyncio.sleep(mx * 2)
            await protocol.close()

        self._loop.create_task(close())

        return protocol

    async def stop(self):
        if self.__started:
            await self._protocol.close()

            self._protocol = None
            self._transport = None
            self.__started = False

    # Properties
    @property
    def started(self):
        return self.__started
