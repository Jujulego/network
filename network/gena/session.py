import aiohttp
import asyncio

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
        self._subscriptions = {}  # type: Dict[str, GENASubscription]

    # Methods
    async def _request(self, method: str, event: str, headers: Dict[str, str]):
        assert self._session is not None, 'GENA session must be opened !'

        # Send request
        res = await self._session.request(method, event, headers=headers)

        # Parse response
        if res.status == 200:
            return res

        # Errors
        if res.status == 400:
            raise GENAError(400, 'Incompatible header fields')

        elif res.status == 412:
            raise GENAError(412, 'Precondition Failed')

        elif method == 'SUBSCRIBE' and 500 <= res.status < 600:
            raise GENAError(res.status, 'Unable to accept renewal')

        else:
            raise GENAError(res.status, 'Unknown error')

    async def open(self):
        self._session = aiohttp.ClientSession()
        self._subscriptions = {}

        if not self._server.started:
            await self._server.start()

    async def handler(self, request: web.BaseRequest):
        pass

    async def subscribe(self, event: str, *variables: str, timeout: int = 1800) -> GENASubscription:
        # Request
        res = await self._request('SUBSCRIBE', event, {
            'NT': 'upnp:event',
            'CALLBACK': self._callback,
            'TIMEOUT': f'Second-{timeout}',
            'STATEVAR': ','.join(variables)
        })

        # Parse answer
        sub = GENASubscription(event, res)
        self._subscriptions[sub.id] = sub

        return sub

    async def renew(self, sub: GENASubscription, *, timeout: Optional[int] = None) -> GENASubscription:
        assert not sub.expired, 'GENA subscription has expired'

        if timeout is None:
            timeout = sub.timeout

        # Request
        res = await self._request('SUBSCRIBE', sub.event, {
            'SID': f'uuid:{sub.id}',
            'TIMEOUT': f'Second-{timeout}'
        })

        # Parse answer
        sub._update(res)
        return sub

    async def unsubscribe(self, sub: GENASubscription) -> GENASubscription:
        if sub.expired:
            return sub

        # Request
        await self._request('UNSUBSCRIBE', sub.event, {
            'SID': f'uuid:{sub.id}',
        })

        # Success
        sub._end()
        del self._subscriptions[sub.id]

        return sub

    async def close(self):
        # Unsubscribe all subscriptions
        await asyncio.gather(
            self.unsubscribe(sub) for sub in self._subscriptions.values()
        )

        # Close session
        await self._session.close()
        self._session = None
