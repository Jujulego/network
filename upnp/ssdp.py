import asyncio
import logging

from module import Module, argument, command
from network.ssdp import SSDPServer, SSDPRemoteDevice, SSDPMessage
from network.typing import Address
from typing import Dict


# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4


# Class
class SSDPModule(Module):
    def __init__(self, *, loop=None):
        super().__init__(loop=loop)
        self._searching = False
        self._devices = {}  # type: Dict[str, SSDPRemoteDevice]

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)
        self.ssdp.on('response', self.on_adv_message)
        self.ssdp.on('notify', self.on_adv_message)

    # Methods
    async def init(self):
        await self.ssdp.start()
        super().init()

    def _stop_searching(self):
        self._searching = False

    # Commands
    @command(description="Send a ssdp search")
    @argument('st', nargs='?', default='ssdp:all')
    @argument('--mx', choices=[1, 2, 3, 4, 5])
    async def search(self, reader, writer, st: str, mx: int = 5):
        self._searching = True
        self._loop.call_later(30, self._stop_searching)
        self.ssdp.search(st, mx)

    @command(description="Print device list")
    async def devices(self, reader, writer):
        for d in self._devices.values():
            writer.write(f'{d.address[0]} ({d.state}): {d.uuid}\n')

    @command(description="Quit server")
    async def quit(self, reader, writer):
        self.ssdp.stop()
        self._loop.stop()

    # Callbacks
    def on_adv_message(self, msg: SSDPMessage, addr: Address):
        uuid = msg.usn.uuid

        if uuid not in self._devices:
            print(f'New device on {addr[0]}: {uuid}')
            self._devices[uuid] = SSDPRemoteDevice(msg, addr, loop=self._loop)

        else:
            self._devices[uuid].message(msg)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    ssdp = SSDPModule(loop=loop)

    loop.run_until_complete(ssdp.init())
    loop.run_forever()
