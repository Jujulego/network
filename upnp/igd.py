import argparse
import asyncio
import logging
import sys

from network.ssdp import SSDPMessage, SSDPRemoteDevice
from network.utils.style import style as _s
from typing import List, Optional

from upnp.base import BaseUPnP

# Constants
IGD_URN = 'urn:schemas-upnp-org:device:InternetGatewayDevice:1'


# Class
class IGD(BaseUPnP):
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop=loop)

        # Callbacks
        self.store.on('new', self.on_new_device)
        self.store.on('up', self.on_up_device)

    # Methods
    async def init(self):
        await super().init()

    async def _search(self, event):
        protocol = await self.ssdp.search(IGD_URN)

        @protocol.on('disconnected')
        def disconnected():
            event.set()

    async def search(self):
        event = asyncio.Event()
        task = self._loop.create_task(self._search(event))

        await task
        await event.wait()

    def gateways(self) -> List[SSDPRemoteDevice]:
        return list(filter(lambda device: device.type == IGD_URN, self.store))

    # Callbacks
    def on_new_device(self, device: SSDPRemoteDevice):
        if device.type == IGD_URN:
            print(f'{_s.bold}New device:{_s.reset} {repr(device)}')

    def on_up_device(self, device: SSDPRemoteDevice, msg: SSDPMessage):
        if device.type == IGD_URN:
            print(f'{_s.bold}Up device:{_s.reset} {repr(device)} ({msg.kind})')


async def main(loop: asyncio.AbstractEventLoop):
    # Init service
    igd = IGD(loop=loop)
    await igd.init()

    # Find gateways
    await igd.search()
    gateways = igd.gateways()

    print('Gateways :')
    for gateway in gateways:
        print(f'- {gateway}')

    print(f'{len(gateways)} gateway(s)')
    loop.stop()


if __name__ == '__main__':
    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-color", action="store_true")
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
    loop.run_until_complete(main(loop))
    loop.run_forever()
