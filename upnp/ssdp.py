import argparse
import asyncio
import logging
import sys

from aioconsole import interact, get_standard_streams
from aioconsole.server import parse_server
from network.ssdp import SSDPMessage, SSDPServer, SSDPStore, SSDPRemoteDevice
from network.utils.style import style as _s
from typing import Optional


# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4


# Class
class SSDP:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._searching = False

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)

        self.store = SSDPStore(loop=loop)
        self.store.connect_to(self.ssdp)

        self.store.on('new', self.on_new_device)
        self.store.on('up', self.on_up_device)
        self.store.on('down', self.on_down_device)

    # Methods
    async def init(self):
        await self.ssdp.start()

    def on_new_device(self, device: SSDPRemoteDevice):
        print(f'{_s.bold}New device:{_s.reset} {repr(device)}')

    def on_up_device(self, device: SSDPRemoteDevice, msg: SSDPMessage):
        print(f'{_s.bold}Up device:{_s.reset} {repr(device)} ({"response" if msg.is_response else "notify"})')

    def on_down_device(self, device: SSDPRemoteDevice):
        print(f'{_s.bold}Down device:{_s.reset} {repr(device)}')


async def start_cli(streams=None, *, loop=None):
    await interact(
        streams=streams or get_standard_streams(use_stderr=False, loop=loop),
        locals={
            'ssdp': ssdp.ssdp,
            'store': ssdp.store
        },
        loop=loop
    )


if __name__ == '__main__':
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-cli", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    parser.add_argument("--serve", metavar="[host:]port", type=int)
    parser.add_argument("--verbose", "-v", action="count", default=0)

    args = parser.parse_args(sys.argv[1:])

    if args.no_color:
        _s.enabled = False

    if args.verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose >= 1:
        logging.basicConfig(level=logging.INFO)

    # Start !
    loop = asyncio.get_event_loop()

    ssdp = SSDP(loop=loop)
    loop.run_until_complete(ssdp.init())

    # CLI setup
    if not args.no_cli:
        if args.serve:
            host, port = parse_server(args.serve, parser)
            task = asyncio.start_server(lambda r, w: start_cli(streams=(r, w)), host, port, loop=loop)
        else:
            task = start_cli()

        loop.run_until_complete(task)

    loop.run_forever()
