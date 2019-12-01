from network.http import HTTPCapability
from network.ssdp.urn import URN
from typing import Dict

from .error import SOAPError
from .request import SOAPRequest
from .response import SOAPResponse


class SOAPCapability(HTTPCapability):
    # Methods
    async def soap_call(self, control_url: str, service_type: URN, action: str, arguments: Dict[str, str]) -> Dict[str,str]:
        req = SOAPRequest(control_url, service_type, action, arguments)
        rep = await self.soap_send(req)

        if rep.is_error:
            raise SOAPError(rep.error_code, rep.error_description)

        return rep.results

    async def soap_send(self, request: SOAPRequest) -> SOAPResponse:
        headers = request.headers()
        body = request.body()

        async with self.http_session.post(request.control_url, headers=headers, data=body) as resp:
            is_error = (resp.status == 500)
            data = await resp.text(encoding='utf-8')

            return SOAPResponse(
                request.service_type, request.action,
                data, is_error=is_error
            )
