from network.http import HTTPCapability

from .request import SOAPRequest
from .response import SOAPResponse


class SOAPCapability(HTTPCapability):
    # Methods
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
