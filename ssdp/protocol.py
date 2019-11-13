import asyncio
import logging
import socket
import struct

from typing import Callable, Optional, Union, Text
from utils import Address

from .message import SSDPMessage

# Logging
logger = logging.getLogger("ssdp")

# Typings
MessageCallback = Callable[[SSDPMessage, Address], None]


# Class
class SSDPProtocol(asyncio.DatagramProtocol):
    """
    Receive SSDP messages from the given multicast
    """

    def __init__(self, multicast: Address, *, ttl: int = 4, on_message: Optional[MessageCallback] = None):
        self.transport = None  # type: Optional[asyncio.transports.DatagramTransport]
        self.on_message = on_message

        # parameters
        self.multicast = multicast
        self.ttl = ttl

    # Methods
    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        self.transport = transport
        sock = transport.get_extra_info('socket')

        # subscribe to multicast
        mreq = struct.pack('4sl', socket.inet_aton(self.multicast[0]), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # setup ttl
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.ttl)

        # logging
        logger.info(f'Connected to {self.multicast[0]}:{self.multicast[1]}')

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.transport = None

        # logging
        logger.info(f'Disconnected from {self.multicast[0]}:{self.multicast[1]}')

    def datagram_received(self, data: Union[bytes, Text], addr: Address) -> None:
        # logging
        logger.debug(f'recv {addr[0]}:{addr[1]} => {data}')

        if self.on_message is not None:
            self.on_message(SSDPMessage(message=data.decode('utf-8')), addr)

    def send_message(self, msg: SSDPMessage):
        assert self.transport is not None

        data = msg.message.encode()

        for _ in range(5):
            self.transport.sendto(data, self.multicast)

        # logging
        logger.debug(f'send {data}')

    def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None
