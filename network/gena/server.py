import aiohttp
import logging

from aiohttp import web
from network.base.session import BaseSession
from network.utils.str import generate_random_str
from typing import Dict, Optional

# Constants
CALLBACK_SIZE = 10

# Logging
logger = logging.getLogger('gena')


# Class
class GENAServer:
    def __init__(self):
        # Attributes
        self._server = web.Server(self._handler)
        self._site = None  # type: Optional[web.TCPSite]
        self._runner = None  # type: Optional[web.ServerRunner]
        self._sessions = {}  # type: Dict[str, GENASession]

    # Methods
    def _gen_callback(self) -> str:
        cb = None

        while cb is None or cb in self._sessions:
            cb = generate_random_str(CALLBACK_SIZE)

        return cb

    async def _handler(self, request: web.BaseRequest) -> web.StreamResponse:
        logger.debug(f'{request.host} => {repr(request.content)}')

        if request.method == 'NOTIFY':
            cb = request.path.strip('/')
            session = self._sessions.get(cb)

            if session is not None:
                await session.handler(request)
            else:
                logger.warning(f'Received notify for unknown callback: {cb}')

        return web.Response(status=200)

    async def start(self):
        if self._runner is None:
            # Runner
            self._runner = web.ServerRunner(self._server)
            await self._runner.setup()

            # Site
            self._site = web.TCPSite(self._runner)

        # Start site
        await self._site.start()
        logger.info(f'GENA server started: {self._site.name}')

    def get_session(self) -> 'GENASession':
        cb = self._gen_callback()
        session = GENASession(cb, self)

        self._sessions[cb] = session

        return session

    async def stop(self):
        if self._runner is None:
            return

        await self._runner.cleanup()
        logger.info('GENA server stopped')

    # Properties
    @property
    def started(self) -> bool:
        return self._runner is not None

    @property
    def url(self) -> Optional[str]:
        if self._site is not None:
            return None

        return self._site.name


# Class
class GENASession(BaseSession):
    def __init__(self, callback: str, server: GENAServer):
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
