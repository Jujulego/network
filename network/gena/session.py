import aiohttp

from aiohttp import web
from network.base.session import BaseSession
from network.base.server import BaseServer
from typing import Optional


# Class
class GENASession(BaseSession):
    def __init__(self, callback: str, server: BaseServer):
        # Attributes
        self._callback = callback

        self._server = server
        self._session = None  # type: Optional[aiohttp.ClientSession]

    # Methods
    async def open(self):
        self._session = aiohttp.ClientSession()

        if not self._server.started:
            await self._server.start()

    async def handler(self, request: web.BaseRequest):
        pass

    async def subscribe(self, event: str, *vars: str, timeout: int = 3600):
        assert self._session is not None, 'GENA session must be opened !'

        # Send request
        await self._session.request(
            'SUBSCRIBE', event,
            headers={
                'CALLBACK': self._callback,
                'NT': 'upnp:event',
                'TIMEOUT': f'Second-{timeout}',
                'STATEVAR': ','.join(vars)
            }
        )

    async def close(self):
        await self._session.close()
        self._session = None
