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

    async def search(self):
        return await self.ssdp.search(IGD_URN)

    def gateways(self) -> List[SSDPRemoteDevice]:
        return list(filter(lambda device: device.type == IGD_URN, self.store))

    # Callbacks
    def on_new_device(self, device: SSDPRemoteDevice):
        if device.type == IGD_URN:
            print(f'{_s.bold}New device:{_s.reset} {repr(device)}')

    def on_up_device(self, device: SSDPRemoteDevice, msg: SSDPMessage):
        if device.type == IGD_URN:
            print(f'{_s.bold}Up device:{_s.reset} {repr(device)} ({msg.kind})')


async def main():
    # Init service
    igd = IGD()
    await igd.init()

    # Find gateways
    protocol = await igd.search()

    @protocol.on('disconnected')
    def disconnected():
        gateways = igd.gateways()

        print('Gateways :')
        for gateway in gateways:
            print(f'- {gateway}')

        print(f'{len(gateways)} gateway(s)')


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
    loop.run_until_complete(main())
    loop.run_forever()
