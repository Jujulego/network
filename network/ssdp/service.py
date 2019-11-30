import asyncio

from enum import Enum, auto
from network.http.capability import HTTPCapability
from network.utils.machine import StateMachine
from typing import Dict, Optional
from xml.etree import ElementTree as ET

# Constants
XML_DEVICE_NS = {
    'upnp': 'urn:schemas-upnp-org:device-1-0'
}
XML_SERVICE_NS = {
    'upnp': 'urn:schemas-upnp-org:service-1-0'
}


# Utils
def xml_text(e: Optional[ET.Element]) -> Optional[str]:
    return None if e is None else e.text


# States
class SState(Enum):
    UP = auto()
    DOWN = auto()


# Classes
class SSDPService(StateMachine, HTTPCapability):
    def __init__(self, xml: ET.Element, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        StateMachine.__init__(self, SState.DOWN, loop=loop)
        HTTPCapability.__init__(self, loop=loop)

        # Parse xml
        self.id = xml.find('upnp:serviceId', XML_DEVICE_NS).text
        self.type = xml.find('upnp:serviceType', XML_DEVICE_NS).text
        self.scdp = xml.find('upnp:SCDPURL', XML_DEVICE_NS).text
        self.control = xml.find('upnp:controlURL', XML_DEVICE_NS).text
        self.event_sub = xml.find('upnp:eventSubURL', XML_DEVICE_NS).text

        # - internals
        self._actions = {}  # type: Dict[str, Action]
        self._state_vars = {}  # type: Dict[str, StateVariable]

        self.__up_task = None  # type: Optional[asyncio.Task]

    def __repr__(self):
        return f'<SSDPService: {self.id}>'

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, SSDPService):
            return self.id == other.id

        return False

    # Methodes
    def up(self):
        if self.state == SState.DOWN:
            if self.__up_task is None or self.__up_task.done():
                self.__up_task = self._loop.create_task(self._up())

    async def _up(self):
        xml = await self._get_description()

        # Gather actions
        self._actions = {}
        for child in xml.find('upnp:actionList', XML_SERVICE_NS):
            action = Action(child, self)

            self._actions[action.name] = action

        # Gather state
        self._state_vars = {}
        for child in xml.find('upnp:serviceStateTable', XML_SERVICE_NS):
            state_var = StateVariable(child, self)

            self._state_vars[state_var.name] = state_var

        # Service is ready to be used
        self.state = SState.UP

    async def _get_description(self) -> ET.Element:
        async with self.http_get(self.scdp) as response:
            assert response.status == 200, f'Unable to get description (status {response.status})'
            data = await response.read()

            return ET.fromstring(data.decode('utf-8'))

    def down(self):
        if self.state == SState.UP:
            self.state = SState.DOWN

            if self.__up_task is not None:
                self.__up_task.cancel()


class Action:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self.arguments = [
            Argument(child, service)
            for child in xml.find('upnp:argumentList', XML_SERVICE_NS)
        ]

        # - internals
        self._service = service

    def __repr__(self):
        return f'<Action: {self.name}>'


class Argument:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self.direction = xml.find('upnp:direction', XML_SERVICE_NS).text
        self.retval = xml.find('upnp:retval', XML_SERVICE_NS) is not None

        # - internals
        self._service = service
        self._related_state_var = xml.find('upnp:relatedStateVariable', XML_SERVICE_NS).text

    def __repr__(self):
        return f'<Argument: {self.name}>'


class StateVariable:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.send_events = xml.attrib['sendEvents'] == 'yes'
        self.multicast = xml.attrib['multicast'] == 'yes'

        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self.default_value = xml_text(xml.find('upnp:defaultValue', XML_SERVICE_NS))

        xavl = xml.find('upnp:allowedValueList', XML_SERVICE_NS)
        self.allowed_values = [child.text for child in xavl or None]

        xavr = xml.find('upnp:allowedValueRange', XML_SERVICE_NS)
        self.allowed_range = None if xavr is None else ValueRange(xavr)

        xtype = xml.find('upnp:dataType', XML_SERVICE_NS)
        self.type = xtype.attrib.get('type', xtype.text)

        # - internals
        self._service = service

    def __repr__(self):
        return f'<StateVariable: {self.name}>'


class ValueRange:
    def __init__(self, xml: ET.Element):
        self._minimum = xml.find('upnp:minimum', XML_SERVICE_NS).text
        self._maximum = xml.find('upnp:maximum', XML_SERVICE_NS).text
        self._step = xml_text(xml.find('upnp:step', XML_SERVICE_NS))
