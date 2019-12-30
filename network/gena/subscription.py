import asyncio

from aiohttp import ClientResponse
from network.base.machine import StateMachine
from typing import Optional


# Class
class GENASubscription(StateMachine):
    def __init__(self, event: str, res: ClientResponse):
        super().__init__('valid')

        # Attributes
        self.event = event
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
    def _end(self):
        self.state = 'invalid'

    def _update(self, res: ClientResponse):
        # Parse response
        self.id = res.headers.getone('SID')
        self.date = res.headers.getone('DATE', None)
        self.timeout = int(res.headers.getone('TIMEOUT')[7:])
        self.variables = res.headers.getone('ACCEPTED-STATEVAR', '').split(',')

        # Automatic timeout
        if self.__invalid_handle is not None:
            self.__invalid_handle.cancel()

        loop = asyncio.get_running_loop()
        self.__invalid_handle = loop.call_later(self.timeout, self._end)
