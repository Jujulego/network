import argparse
import asyncio
import logging
import socket
import sys

from aiohttp import web
from network.soap import SOAPError
from network.ssdp import SSDPServer, SSDPStore, SSDPRemoteDevice
from network.utils.style import style as _s
from pprint import pprint
from typing import List

# Constants
APP_PORT = 8000

MULTICAST = ("239.255.255.250", 1900)
TTL = 4

IGD_URNS = [
    'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
    'urn:schemas-upnp-org:device:InternetGatewayDevice:2'
]
WANIP_URN = 'urn:schemas-upnp-org:service:WANIPConn1'


# Class
class IGD:
    def __init__(self):
        # Attributes
        self._loop = asyncio.get_event_loop()
        self._searching = False

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL)

        self.store = SSDPStore()
        self.store.connect_to(self.ssdp)

    # Methods
    async def init(self):
        await self.ssdp.start()

    async def search(self):
        protocol = await self.ssdp.search(*IGD_URNS)
        await protocol.wait('disconnected')

    async def stop(self):
        await self.ssdp.stop()

    def gateways(self) -> List[SSDPRemoteDevice]:
        return list(filter(lambda device: device.type in IGD_URNS, self.store))


def get_ip(device: SSDPRemoteDevice) -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect((device.address, 80))
        return s.getsockname()[0]

    finally:
        s.close()


async def main():
    print('Searching for gateways ...')

    # Init ssdp service
    igd = IGD()
    await igd.init()

    # Find gateways
    await igd.search()
    gws = igd.gateways()

    print('Gateways :')
    for gw in gws:
        print(f'- {gw}')

    print(f'{len(gws)} gateway(s)')

    if len(gws) == 0:
        print(_s.red('No gateway found'))

        return

    # Stop ssdp discovery
    await igd.stop()

    # Get service
    gw = gws[0]
    service = gw.children[0].children[0].service('urn:upnp-org:serviceId:WANIPConn1')

    # Get internal ip to the gateway
    ip = get_ip(gw)

    try:
        # Get external ip address
        result = await service.action('GetExternalIPAddress')()
        ext_ip = result['NewExternalIPAddress']

        # Open external port
        await service.action('AddPortMapping')(
            NewRemoteHost='',
            NewExternalPort=APP_PORT,
            NewProtocol='TCP',
            NewInternalPort=APP_PORT,
            NewInternalClient=ip,
            NewEnabled='1',
            NewPortMappingDescription='test igd',
            NewLeaseDuration=3600
        )
    except SOAPError as err:
        print(_s.red(f'SOAPError: {err}'))

        return

    # Web server
    routes = web.RouteTableDef()

    @routes.get('/')
    async def hello(request: web.Request):
        print(request)
        return web.Response(text="Hello, world")

    app = web.Application()
    app.add_routes(routes)

    # Run server
    runner = web.AppRunner(app)
    await runner.setup()

    print(f'Web server available at http://{ext_ip}:{APP_PORT}/')
    site = web.TCPSite(runner, host=ip, port=APP_PORT)
    await site.start()

    await asyncio.sleep(10 * 60)
    await runner.cleanup()


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

    # Run !
    asyncio.run(main())
