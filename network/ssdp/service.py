import aiohttp
import asyncio
import logging

from enum import Enum, auto
from network.soap import SOAPCapability
from network.utils.machine import StateMachine
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from .constants import XML_DEVICE_NS, XML_SERVICE_NS
from .urn import URN
from .types import SSDPType, get_type


# Utils
def xml_text(e: Optional[ET.Element]) -> Optional[str]:
    return None if e is None else e.text


# States
class SState(Enum):
    UP = auto()
    DOWN = auto()


# Classes
class SSDPService(StateMachine, SOAPCapability):
    def __init__(self, xml: ET.Element, base_url: str, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        StateMachine.__init__(self, SState.DOWN, loop=loop)
        SOAPCapability.__init__(self, loop=loop)

        # Parse xml
        self.id = xml.find('upnp:serviceId', XML_DEVICE_NS).text
        self.type = URN(xml.find('upnp:serviceType', XML_DEVICE_NS).text)
        self.scpd = urljoin(base_url, xml.find('upnp:SCPDURL', XML_DEVICE_NS).text)
        self.control = urljoin(base_url, xml.find('upnp:controlURL', XML_DEVICE_NS).text)
        self.event_sub = urljoin(base_url, xml.find('upnp:eventSubURL', XML_DEVICE_NS).text)

        # - internals
        self._actions = {}  # type: Dict[str, Action]
        self._state_vars = {}  # type: Dict[str, StateVariable]
        self._logger = logging.getLogger(f'ssdp:service:{self.id}')

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
    async def call(self, action: Union[str, 'Action'], args: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(action, str):
            action = self.action(action)

        # Convert arguments
        soap_args = {}

        for n, v in args.items():
            var = action.argument(n).state_variable
            soap_args[n] = var.type.from_python(v)

        # Request
        results = await self.soap_call(self.control, self.type.urn, action.name, soap_args)

        # Convert response
        py_resp = {}

        for n, v in results.items():
            var = action.argument(n).state_variable
            py_resp[n] = var.type.to_python(v)

        return py_resp

    def up(self):
        if self.state == SState.DOWN:
            if self.__up_task is None or self.__up_task.done():
                self.__up_task = self._loop.create_task(self._up())

    async def _up(self):
        self._logger.info('Getting description')

        try:
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
            self._logger.info('Ready !')

        except aiohttp.ClientError as err:
            self._logger.error(f'Error while getting description: {err}')

        except Exception:
            self._logger.exception(f'Error while parsing description ({self.scpd})')

    async def _get_description(self) -> ET.Element:
        async with aiohttp.ClientSession(loop=self._loop) as session:
            async with session.get(self.scpd) as response:
                assert response.status == 200, f'Unable to get description (status {response.status})'
                data = await response.read()

                return ET.fromstring(data.decode('utf-8'))

    def down(self):
        if self.state == SState.UP:
            self.state = SState.DOWN

            if self.__up_task is not None:
                self.__up_task.cancel()

    def action(self, name: str) -> 'Action':
        return self._actions[name]

    def state_variable(self, name: str) -> 'StateVariable':
        return self._state_vars[name]

    # Properties
    @property
    def actions(self) -> List['Action']:
        return list(self._actions.values())

    @property
    def state_variables(self) -> List['StateVariable']:
        return list(self._state_vars.values())


class Action:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self._arguments = {}  # type: Dict[str, Argument]

        for child in xml.find('upnp:argumentList', XML_SERVICE_NS):
            arg = Argument(child, service)
            self._arguments[arg.name] = arg

        # - internals
        self._service = service

    def __repr__(self):
        return f'<Action: {self.name}>'

    def __call__(self, **kwargs):
        return self.call(**kwargs)

    # Methods
    def argument(self, name: str) -> 'Argument':
        return self._arguments[name]

    async def call(self, **kwargs) -> Dict[str, Any]:
        # check args
        for n in kwargs:
            assert n in self._arguments

        # call
        return await self._service.call(self, kwargs)

    # Properties
    @property
    def arguments(self) -> List['Argument']:
        return list(self._arguments.values())

    @property
    def parameters(self) -> List['Argument']:
        return list(filter(
            lambda arg: arg.direction == 'in',
            self._arguments.values()
        ))

    @property
    def results(self) -> List['Argument']:
        return list(filter(
            lambda arg: arg.direction == 'out',
            self._arguments.values()
        ))


class Argument:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self.direction = xml.find('upnp:direction', XML_SERVICE_NS).text
        self.retval = xml.find('upnp:retval', XML_SERVICE_NS) is not None

        # - internals
        self._service = service
        self._state_variable = xml.find('upnp:relatedStateVariable', XML_SERVICE_NS).text

    def __repr__(self):
        return f'<Argument: {self.name}>'

    # Properties
    @property
    def state_variable(self):
        return self._service.state_variable(self._state_variable)


class StateVariable:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.send_events = xml.attrib.get('sendEvents', 'yes') == 'yes'
        self.multicast = xml.attrib.get('multicast', 'no') == 'yes'

        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self.default_value = xml_text(xml.find('upnp:defaultValue', XML_SERVICE_NS))

        xtype = xml.find('upnp:dataType', XML_SERVICE_NS)
        self.type = get_type(xtype.attrib.get('type', xtype.text))

        xavl = xml.find('upnp:allowedValueList', XML_SERVICE_NS)
        if xavl is not None:
            self.allowed_values = [
                self.type.to_python(child.text)
                for child in xavl or None
            ]
        else:
            self.allowed_values = None

        xavr = xml.find('upnp:allowedValueRange', XML_SERVICE_NS)
        self.allowed_range = None if xavr is None else ValueRange(xavr, self.type)

        # - internals
        self._service = service

    def __repr__(self):
        return f'<StateVariable: {self.name}>'


class ValueRange:
    def __init__(self, xml: ET.Element, stype: SSDPType):
        self.minimum = stype.from_python(xml.find('upnp:minimum', XML_SERVICE_NS).text)
        self.maximum = stype.from_python(xml.find('upnp:maximum', XML_SERVICE_NS).text)

        step = xml_text(xml.find('upnp:step', XML_SERVICE_NS))
        self.step = stype.from_python(step)
