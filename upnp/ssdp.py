import asyncio
import logging

from network.stream.console import Console
from network.ssdp import SSDPServer

# Parameters
MULTICAST = ("239.255.255.250", 1900)
TTL = 4

# Logging
logging.basicConfig(level=logging.DEBUG)


# Class
class SSDPUtility:
    def __init__(self, *, loop=None):
        self._loop = loop or asyncio.get_event_loop()
        self._searching = False

        # - console
        self.console = Console(loop=self._loop)
        self.console.on('input', self.cmd)

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)
        self.ssdp.on('response', self.response)
        self.ssdp.on('search', self.search)

    # Methods
    def _stop_searching(self):
        self._searching = False

    async def start(self):
        await self.ssdp.start()
        await self.console.start()

    # Callbacks
    def cmd(self, line):
        if line == '':
            return

        if line == 'search':
            self._searching = True
            self._loop.call_later(30, self._stop_searching)
            self.ssdp.search('ssdp:all')
        elif line == 'quit':
            self.ssdp.stop()
            self.console.stop()
            self._loop.stop()
        else:
            print(f'Unknown command : {line}')

    def response(self, msg, addr):
        if self._searching:
            print(f'{addr[0]}: {msg.usn}')

    def search(self, msg, addr):
        print(f'{addr[0]}: search for {msg.st}')


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    utility = SSDPUtility(loop=loop)

    loop.run_until_complete(utility.start())
    loop.run_forever()
