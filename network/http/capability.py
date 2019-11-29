import aiohttp
import asyncio

from typing import Optional


class HTTPCapability:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self.__session = aiohttp.ClientSession(loop=loop)

    # Methods
    def http_get(self, url: str):
        return self.http_session.get(url)

    # Properties
    @property
    def http_session(self) -> aiohttp.ClientSession:
        return self.__session
