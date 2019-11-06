import asyncio
import logging
import socket
import struct

from typing import Callable, Optional, Union, Text, Tuple

from .message import SSDPMessage

# Logging
logger = logging.getLogger("ssdp")

# Typings
MessageCallback = Callable[[SSDPMessage], None]


# Class
class SSDPProtocol(asyncio.DatagramProtocol):
    """
    Receive SSDP messages from the given multicast
    """

    def __init__(self, multicast: str, port: int, *, ttl: int = 4, on_message: Optional[MessageCallback] = None):
        self.transport = None  # type: Optional[asyncio.transports.BaseTransport]
        self.on_message = on_message

        # parameters
        self.multicast = multicast
        self.port = port
        self.ttl = ttl

    # Methods
    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        self.transport = transport
        sock = transport.get_extra_info('socket')

        # subscribe to multicast
        mreq = struct.pack('4sl', socket.inet_aton(self.multicast), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        # setup ttl
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, self.ttl)

        # logging
        logger.info("Connected to %s:%d", self.multicast, self.port)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.transport = None

    def datagram_received(self, data: Union[bytes, Text], addr: Tuple[str, int]) -> None:
        # logging
        logger.debug("%s:%d => %s", addr[0], addr[1], data)

        if self.on_message is not None:
            msg = SSDPMessage(data.decode('utf-8'), addr)
            self.on_message(msg)
