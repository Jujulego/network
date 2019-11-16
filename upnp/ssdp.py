import aioconsole
import argparse
import asyncio
import logging

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

        # - ssdp
        self.ssdp = SSDPServer(MULTICAST, ttl=TTL, loop=self._loop)
        self.ssdp.on('response', self.on_response)
        self.ssdp.on('search', self.on_search)

    # Methods
    def _make_cli(self, streams=None) -> aioconsole.AsynchronousCli:
        # - quit
        quit_parser = argparse.ArgumentParser(description="Quit server")

        # - search
        search_parser = argparse.ArgumentParser(description="Send a ssdp search")
        search_parser.add_argument('st', type=str, nargs='?', default="ssdp:all")
        search_parser.add_argument('--mx', type=int, default=5, choices=[1, 2, 3, 4, 5])

        return aioconsole.AsynchronousCli({
            'quit': (self.quit, quit_parser),
            'search': (self.search, search_parser)
        }, streams=streams)

    def _stop_searching(self):
        self._searching = False

    async def start(self):
        await self.ssdp.start()
        asyncio.ensure_future(self._make_cli().interact())

    # Commands
    async def quit(self, reader, writer):
        self.ssdp.stop()
        self._loop.stop()

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
    loop = asyncio.get_event_loop()
    utility = SSDPUtility(loop=loop)

    loop.run_until_complete(utility.start())
    loop.run_forever()
