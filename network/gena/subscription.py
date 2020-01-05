import asyncio

from aiohttp import web, ClientResponse
from network.base.machine import StateMachine
from typing import Dict, Optional
from xml.etree import ElementTree as ET

from .constants import XML_GENA_NS


# Class
class GENASubscription(StateMachine):
    """
    class GENASubscription:
    Represent and manage a GENA subscription.

    Events:
    - update (values: Dict[str, str], seq: int) : each time a new value is emitted
    - expired (was: str)                        : each time the subscription goes expired
    """

    def __init__(self, event: str, res: ClientResponse):
        super().__init__('valid')

        # Attributes
        self.event = event
        self._seq = 0
        self._values = {}  # type: Dict[str, str]
        self.__invalid_handle = None  # type: Optional[asyncio.TimerHandle]

        # Parse response
        self._update(res)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, GENASubscription):
            return self.event == other.event and self.id == other.id

        return False

    # Methods
    def _parse_xml(self, xml: ET.Element) -> Dict[str, str]:
        pset = xml.find('event:propertyset', XML_GENA_NS)
        values = {}

        for prop in pset.findall('event:property', XML_GENA_NS):
            var = list(prop)[0]

            values[var.tag] = var.text

        return values

    async def _handler(self, request: web.BaseRequest):
        nt = request.headers.getone('NT')
        nts = request.headers.getone('NTS')

        if nt == 'upnp:event' and nts == 'upnp:propchange':
            seq = int(request.headers.getone('SEQ'))

            if seq == 0 or seq > self._seq:
                data = await request.read()
                xml = ET.fromstring(data)

                self._seq = seq
                self._values = self._parse_xml(xml)

                self.emit('update', self._values, seq=seq)

    def _update(self, res: ClientResponse):
        # Parse response
        self.id = res.headers.getone('SID')[5:]
        self.date = res.headers.getone('DATE', None)
        self.timeout = int(res.headers.getone('TIMEOUT')[7:])
        self.variables = res.headers.getone('ACCEPTED-STATEVAR', '').split(',')

        # Automatic timeout
        if self.__invalid_handle is not None:
            self.__invalid_handle.cancel()

        loop = asyncio.get_running_loop()
        self.__invalid_handle = loop.call_later(self.timeout, self.__end)

    def _end(self):
        if self.__invalid_handle is not None:
            self.__invalid_handle.cancel()

        self.__end()

    def __end(self):
        self.state = 'expired'

    # Properties
    @property
    def expired(self) -> bool:
        return self.state == 'expired'

    @property
    def seq(self):
        return self._seq

    @property
    def value(self):
        return self._values
