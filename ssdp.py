import asyncio
import logging

from ssdp import SSDPServer

# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4

# Logging
logging.basicConfig(level=logging.DEBUG)

# Prepare server
loop = asyncio.get_event_loop()
ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=loop)


@ssdp.on('message')
def message(msg, addr):
    print(addr, repr(msg))


def search_all():
    ssdp.search("ssdp:all")


if __name__ == '__main__':
    loop.run_until_complete(ssdp.start())
    loop.call_later(10, search_all)
    loop.call_later(30, ssdp.stop)
    loop.run_forever()
