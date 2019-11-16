import asyncio
import logging

from module import Module, argument, command
from network.ssdp import SSDPServer


# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4


# Class
class SSDPModule(Module):
    def __init__(self, *, loop=None):
        super().__init__(loop=loop)
        self._searching = False

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)
        self.ssdp.on('response', self.on_response)
        self.ssdp.on('search', self.on_search)

    # Methods
    async def init(self):
        await self.ssdp.start()
        super().init()

    def _stop_searching(self):
        self._searching = False

    # Commands
    @command(description="Quit server")
    async def quit(self, reader, writer):
        self.ssdp.stop()
        self._loop.stop()

    @command(description="Send a ssdp search")
    @argument('st', nargs='?', default='ssdp:all')
    @argument('--mx', choices=[1, 2, 3, 4, 5])
    async def search(self, reader, writer, st: str, mx: int = 5):
        self._searching = True
        self._loop.call_later(30, self._stop_searching)
        self.ssdp.search(st, mx)

    # Callbacks
    def on_response(self, msg, addr):
        if self._searching:
            print(f'{addr[0]}: {msg.usn}')

    def on_search(self, msg, addr):
        print(f'{addr[0]}: search for {msg.st}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    ssdp = SSDPModule(loop=loop)

    loop.run_until_complete(ssdp.init())
    loop.run_forever()
