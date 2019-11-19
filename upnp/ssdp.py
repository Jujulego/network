import asyncio
import logging

from module import Module, argument, command
from network.ssdp import SSDPServer, SSDPStore, URN
from typing import Optional


# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4


# Class
class SSDPModule(Module):
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop=loop)
        self._searching = False
        self._store = SSDPStore(loop=loop)

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)
        self.ssdp.on('response', self._store.on_adv_message)
        self.ssdp.on('notify', self._store.on_adv_message)

    # Methods
    async def init(self):
        await self.ssdp.start()
        super().init()

    def _stop_searching(self):
        self._searching = False

    # Commands
    @command(description="Send a ssdp search")
    @argument('--mx', choices=[1, 2, 3, 4, 5])
    @argument('st', nargs='?', default='ssdp:all')
    async def search(self, reader, writer, st: str, mx: int = 5):
        self._searching = True
        self._loop.call_later(30, self._stop_searching)
        self.ssdp.search(st, mx)

    @command(description="Print device list")
    @argument('val', nargs='?')
    @argument('--ip', dest='ip', action='store_true')
    @argument('-r', '--root', dest='root', action='store_true')
    async def store(self, reader, writer, val: str = '', ip=False, root=False):
        if root:
            devices = self._store.roots()
        elif val == '':
            devices = self._store
        elif ip:
            devices = self._store.ip_filter(val)
        else:
            devices = self._store.urn_filter(val)

        for d in devices:
            writer.write(f'{d.address[0]} ({d.state}): {d.uuid}\n')

    @command(description="Show device details")
    @argument('uuid')
    async def show(self, reader, writer, uuid: str):
        device = self._store.get(uuid)

        if device is None:
            writer.write(f'No device {uuid}\n')

        else:
            writer.write(f'Device {uuid}:\n')
            writer.write(f'- address  : {device.address[0]}\n')
            writer.write(f'- location : {device.location}\n')
            writer.write(f'- root     : {device.root}\n')
            writer.write(f'\n')
            writer.write(f'URNs :\n')

            for urn in device.urns:
                writer.write(f'- {urn}\n')

    @command(description="Quit server")
    async def quit(self, reader, writer):
        self.ssdp.stop()
        self._loop.stop()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    ssdp = SSDPModule(loop=loop)

    loop.run_until_complete(ssdp.init())
    loop.run_forever()
