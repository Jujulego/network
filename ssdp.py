import asyncio
import logging

from stream.console import Console
from ssdp import SSDPServer

# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4

# Logging
logging.basicConfig(level=logging.INFO)

# Prepare server
loop = asyncio.get_event_loop()
ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=loop)


@ssdp.on('message')
def message(msg, addr):
    pass


# Prepare console
console = Console(loop=loop)


@console.on('input')
def cmd(line):
    if line == '':
        return

    if line == 'search':
        ssdp.search('ssdp:all')
    elif line == 'stop':
        ssdp.stop()
        console.stop()
        loop.stop()
    else:
        print(f'Unknown command : {line}')


if __name__ == '__main__':
    loop.run_until_complete(ssdp.start())
    loop.run_until_complete(console.start())
    loop.run_forever()
