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
        self._loop = loop or asyncio.get_event_loop()
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

    def gateways(self) -> List[SSDPRemoteDevice]:
        return list(filter(lambda device: device.type in IGD_URNS, self.store))


def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

    finally:
        s.close()


async def main(loop: asyncio.AbstractEventLoop, ip: str, port: int):
    # Init service
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
        loop.stop()
        sys.exit(1)

    gw = gws[0]
    service = gw.children[0].children[0].service('urn:upnp-org:serviceId:WANIPConn1')

    try:
        pprint(await service.action('GetExternalIPAddress')())

        if gw.type.version == '2':
            try:
                pprint(await service.action('GetListOfPortMappings')(
                    NewManage='1',
                    NewStartPort=port,
                    NewEndPort=port,
                    NewProtocol='TCP',
                    NewNumberOfPorts='10'
                ))
            except SOAPError as err:
                if err.code != 730:
                    raise
                else:
                    print('No port mapping')

        pprint(await service.action('AddPortMapping')(
            NewRemoteHost='',
            NewExternalPort=port,
            NewProtocol='TCP',
            NewInternalPort=port,
            NewInternalClient=ip,
            NewEnabled='1',
            NewPortMappingDescription='test igd',
            NewLeaseDuration=3600
        ))
    except SOAPError as err:
        print(_s.red(f'SOAPError: {err}'))
        loop.stop()
        sys.exit(1)


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

    # Web server
    routes = web.RouteTableDef()

    @routes.get('/')
    async def hello(request: web.Request):
        return web.Response(text="Hello, world")

    app = web.Application()
    app.add_routes(routes)

    ip = get_ip()
    port = 8080

    # Start !
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop, ip, port))
    web.run_app(app, host=ip, port=port)
    loop.stop()
