import asyncio
import logging
import socket

from network.base.emitter import EventEmitter
from network.typing import Address
from typing import Optional

from .message import SSDPMessage

# Logging
logger = logging.getLogger("ssdp")


# Class
class WindowsSearchProtocol(EventEmitter):
    def __init__(self, multicast: Address, *, ttl: int = 4, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop)

        # Attributes
        self.multicast = multicast
        self.ttl = ttl

        self.future = None  # type: Optional[asyncio.Future]

    # Methods
    def _create_socket(self, request: SSDPMessage) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
        sock.settimeout(request.mx)

        return sock

    def _send_message(self, request: SSDPMessage):
        # Open socket
        sock = self._create_socket(request)

        logger.debug('Search using WindowsSearchProtocol')
        logger.info(f'Connected to {self.multicast[0]}:{self.multicast[1]}')
        self.emit('connected')

        try:
            # Send
            data = request.message.encode()

            for _ in range(5):
                sock.sendto(data, self.multicast)

            logger.debug(f'{self.multicast[0]}:{self.multicast[1]} <= {data}')

            # Receive
            while True:
                data, addr = sock.recvfrom(1024)

                logger.debug(f'{addr[0]}:{addr[1]} => {data}')
                self.emit('recv', SSDPMessage(message=data.decode('utf-8')), addr)

        except socket.timeout:
            pass

        except OSError:
            logger.exception(f'Error while sending search')

        finally:
            # Close socket
            sock.close()

            logger.info(f'Disconnected from {self.multicast[0]}:{self.multicast[1]}')
            self.emit('disconnected')

    def send_message(self, request: SSDPMessage):
        assert request.method == 'M-SEARCH', f'Invalid search request: wrong message kind ({request.kind})'

        self.future = self._loop.run_in_executor(None, self._send_message, request)

    def close(self):
        pass
