import argparse
import asyncio
import logging
import socket
import sys

from network.soap import SOAPError
from network.ssdp import SSDPServer, SSDPStore, SSDPRemoteDevice
from network.utils.style import style as _s
from typing import List

# Constants
APP_PORT = 8000

MULTICAST = ("239.255.255.250", 1900)
TTL = 4

IGD_URNS = [
    'urn:schemas-upnp-org:device:InternetGatewayDevice:1',
    'urn:schemas-upnp-org:device:InternetGatewayDevice:2'
]
WAN_URNS = [
    'urn:schemas-upnp-org:device:WANConnectionDevice:1',
    'urn:schemas-upnp-org:device:WANConnectionDevice:2'
]
WANIP_URNS = [
    'urn:schemas-upnp-org:service:WANIPConnection:1',
    'urn:schemas-upnp-org:service:WANIPConnection:2'
]


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
        event = asyncio.Event()

        @self.store.on('new')
        def wait_gw(device: SSDPRemoteDevice):
            print(f'{_s.bold}New device:{_s.reset} {repr(device)}')

            if device.type in IGD_URNS:
                event.set()

        protocol = await self.ssdp.search(*IGD_URNS)
        await protocol.wait('disconnected')
        await event.wait()

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

    # Get gateway with service
    event = asyncio.Event()

    for gw in gws:
        devices = gw.find_device(*WAN_URNS, in_children=True)

        if len(devices) == 0:
            continue

        device = devices[0]
        services = device.find_service(*WANIP_URNS)

        if len(services) > 0:
            service = services[0]
            break

        @device.on('new')
        def new(service):
            print(f'{_s.bold}New service:{_s.reset} {repr(service)}')

            if service.type in WANIP_URNS:
                event.set()

    else:
        print(_s.yellow('Wait for services'))
        await event.wait()

        for gw in gws:
            services = gw.find_service(*WANIP_URNS, in_children=True)

            if len(services) > 0:
                service = services[0]
                break
        else:
            print(_s.red('No valid gateway found'))
            return

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
