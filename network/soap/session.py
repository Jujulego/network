import aiohttp
import asyncio
import logging

from typing import Dict, Optional

from .error import SOAPError
from .request import SOAPRequest
from .response import SOAPResponse

# Logging
logger = logging.getLogger('soap')


# Class
class SOAPSession:
    def __init__(self):
        # Attributes
        self._session = None  # type: Optional[aiohttp.ClientSession]

    async def __aenter__(self):
        await self.open()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    # Methods
    async def open(self):
        self._session = aiohttp.ClientSession()

    async def call(self, control_url: str, service_type: str, action: str, args: Dict[str, str]) -> Dict[str, str]:
        req = SOAPRequest(control_url, service_type, action, args)
        rep = await self.send(req)

        if rep.is_error:
            raise SOAPError(rep.error_code, rep.error_description)

        return rep.results

    async def send(self, request: SOAPRequest) -> SOAPResponse:
        headers = request.headers()
        body = request.body()

        logger.debug(f'{request.control_url} <= {body}')
        async with self._session.post(request.control_url, headers=headers, data=body) as resp:
            is_error = (resp.status == 500)
            data = await resp.text(encoding='utf-8')

            logger.debug(f'{request.control_url} => {data}')

            return SOAPResponse(
                request.service_type, request.action,
                data, is_error=is_error
            )

    async def close(self):
        await self._session.close()
        self._session = None
