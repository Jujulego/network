import aiohttp
import asyncio


class HTTPCapability:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.__session = aiohttp.ClientSession(loop=loop)

    # Methods
    def http_get(self, url: str):
        return self.http_session.get(url)

    # Properties
    @property
    def http_session(self) -> aiohttp.ClientSession:
        return self.__session
