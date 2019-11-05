import asyncio
import socket
import struct

from typing import Optional, Union, Text, Tuple

from .message import SSDPMessage


class SSDPProtocol(asyncio.DatagramProtocol):
    """
    Receive SSDP messages from the given multicast
    """

    def __init__(self, multicast: str, port: int, ttl: int = 4):
        self.transport = None  # type: Optional[asyncio.transports.BaseTransport]

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

    def connection_lost(self, exc: Optional[Exception]) -> None:
        self.transport = None

    def datagram_received(self, data: Union[bytes, Text], addr: Tuple[str, int]) -> None:
        msg = SSDPMessage(data.decode('utf-8'), addr)

        print(repr(msg))
