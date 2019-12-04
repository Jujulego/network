import aiohttp
import asyncio

from typing import Dict, Optional

from .error import SOAPError
from .request import SOAPRequest
from .response import SOAPResponse


class SOAPCapability:
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        self._loop = loop or asyncio.get_event_loop()

    # Methods
    async def soap_call(self, control_url: str, service_type: str, action: str, args: Dict[str, str]) -> Dict[str, str]:
        req = SOAPRequest(control_url, service_type, action, args)
        rep = await self.soap_send(req)

        if rep.is_error:
            raise SOAPError(rep.error_code, rep.error_description)

        return rep.results

    async def soap_send(self, request: SOAPRequest) -> SOAPResponse:
        headers = request.headers()
        body = request.body()

        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.post(request.control_url, headers=headers, data=body) as resp:
                is_error = (resp.status == 500)
                data = await resp.text(encoding='utf-8')

                return SOAPResponse(
                    request.service_type, request.action,
                    data, is_error=is_error
                )
