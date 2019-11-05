import asyncio

from typing import Optional

from .protocol import SSDPProtocol


async def create_ssdp_endpoint(multicast: str, port: int, ttl: int = 4, loop: Optional[asyncio.AbstractEventLoop] = None):
    if loop is None:
        loop = asyncio.get_event_loop()

    return await loop.create_datagram_endpoint(
        lambda: SSDPProtocol(multicast, port, ttl=ttl),
        local_addr=('0.0.0.0', port),
        reuse_address=True
    )
