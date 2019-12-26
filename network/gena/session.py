import aiohttp

from aiohttp import web
from network.base.session import BaseSession
from network.base.server import BaseServer
from typing import Dict, Optional

from .error import GENAError
from .subscription import GENASubscription


# Class
class GENASession(BaseSession):
    def __init__(self, callback: str, server: BaseServer):
        # Attributes
        self._callback = callback

        self._server = server
        self._session = None  # type: Optional[aiohttp.ClientSession]
        self._subscriptions = {}  # type: Dict[GENASubscription]

    # Methods
    async def open(self):
        self._session = aiohttp.ClientSession()
        self._subscriptions = {}

        if not self._server.started:
            await self._server.start()

    async def handler(self, request: web.BaseRequest):
        pass

    async def subscribe(self, event: str, *variables: str, timeout: int = 1800) -> GENASubscription:
        assert self._session is not None, 'GENA session must be opened !'

        # Send request
        res = await self._session.request(
            'SUBSCRIBE', event,
            headers={
                'CALLBACK': self._callback,
                'NT': 'upnp:event',
                'TIMEOUT': f'Second-{timeout}',
                'STATEVAR': ','.join(variables)
            }
        )

        # Parse response
        if res.status == 200:
            sub = GENASubscription(res)
            self._subscriptions[sub.id] = sub

            return sub

        # Errors
        if res.status == 400:
            raise GENAError(400, 'Incompatible header fields')

        elif res.status == 412:
            raise GENAError(412, 'Precondition Failed')

        elif 500 <= res.status < 600:
            raise GENAError(res.status, 'Unable to accept renewal')

        else:
            raise GENAError(res.status, 'Unknown error')

    async def close(self):
        await self._session.close()
        self._session = None
