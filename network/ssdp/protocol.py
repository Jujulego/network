import asyncio
import logging
import socket
import struct

from network.base.emitter import EventEmitter
from network.typing import Address
from typing import Optional, Union, Text

from .message import SSDPMessage

# Logging
logger = logging.getLogger("ssdp")


# Classes
class SSDPProtocol(asyncio.DatagramProtocol, EventEmitter):
    """
    Receive SSDP messages from the given multicast
    """

    def __init__(self, multicast: Address, ttl: int = 4):
        super().__init__()

        # Attributes
        self.transport = None  # type: Optional[asyncio.transports.DatagramTransport]

        self.multicast = multicast
        self.ttl = ttl

    # Methods
    def connection_made(self, transport: asyncio.transports.DatagramTransport) -> None:
        self.transport = transport
        sock = transport.get_extra_info('socket')

        # subscribe to multicast
        mreq = struct.pack('4sl', socket.inet_aton(self.multicast[0]), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # setup ttl
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)

        # logging

        logger.info(f'Connected to {self.multicast[0]}:{self.multicast[1]}')
        self.emit('connected')

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.transport = None

        # logging
        logger.info(f'Disconnected from {self.multicast[0]}:{self.multicast[1]}')
        self.emit('disconnected')

    def datagram_received(self, data: Union[bytes, Text], addr: Address) -> None:
        # logging
        logger.debug(f'{addr[0]}:{addr[1]} => {data}')
        self.emit('recv', SSDPMessage(message=data.decode('utf-8')), addr)

    def send_message(self, msg: SSDPMessage):
        assert self.transport is not None

        data = msg.message.encode()

        for _ in range(5):
            self.transport.sendto(data, self.multicast)

        # logging
        logger.debug(f'{self.multicast[0]}:{self.multicast[1]} <= {data}')

    def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None


class SSDPSearchProtocol(SSDPProtocol):
    """
    Receive SSDP messages from the given multicast
    """

    # Methods
    def connection_made(self, transport: asyncio.transports.DatagramTransport) -> None:
        self.transport = transport
        sock = transport.get_extra_info('socket')

        # setup ttl
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)

        # logging
        logger.debug('Search using SSDPSearchProtocol')
        logger.info(f'Connected to {self.multicast[0]}:{self.multicast[1]}')
        self.emit('connected')
