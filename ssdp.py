import asyncio
import logging

from ssdp.server import SSDPServer

MULTICAST = ("239.255.255.250", 1900)
TTL = 4

logging.basicConfig(level=logging.DEBUG)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=loop)

    @ssdp.on('message')
    def message(msg, addr):
        print(addr, repr(msg))

    asyncio.ensure_future(ssdp.start())
    loop.run_forever()
