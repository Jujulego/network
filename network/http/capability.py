import aiohttp
import asyncio


class HTTPCapability:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.__session = aiohttp.ClientSession(loop=loop)

    # Methods
    async def http_get(self, url: str, *, timeout: int = 10):
        with aiohttp.ClientTimeout(timeout):
            return self.http_session.get(url)

    # Properties
    @property
    def http_session(self) -> aiohttp.ClientSession:
        return self.__session