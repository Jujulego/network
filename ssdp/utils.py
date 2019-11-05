import asyncio
import socket

from typing import Optional

from .protocol import SSDPProtocol


async def create_ssdp_endpoint(multicast: str, port: int, loop: Optional[asyncio.BaseEventLoop] = None):
    if loop is None:
        loop = asyncio.get_event_loop()

    return await loop.create_datagram_endpoint(
        lambda: SSDPProtocol(multicast, port),
        local_addr=('0.0.0.0', port),
        reuse_address=True
    )
