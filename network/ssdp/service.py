import logging

from network.gena import get_gena_session
from network.soap import SOAPSession
from network.base.machine import StateMachine
from network.utils.style import style as _s
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

from .constants import XML_DEVICE_NS, XML_SERVICE_NS
from .types import SSDPType, get_type
from .urn import URN
from .xml import get_service_id

# Constants
_s_type = _s.bold + _s.purple


# Utils
def xml_text(e: Optional[ET.Element]) -> Optional[str]:
    return None if e is None else e.text


# Classes
class SSDPService(StateMachine):
    def __init__(self, xmld: ET.Element, xmls: ET.Element, base_url: str):
        super().__init__('down')

        # Attributes
        self.id = get_service_id(xmld, base_url)

        # - internals
        self._actions = {}  # type: Dict[str, Action]
        self._state = {}    # type: Dict[str, StateVariable]
        self._logger = logging.getLogger(f'ssdp:service:{self.id}')

        # - protocols
        self._gena = get_gena_session()
        self._soap = SOAPSession()

        # Parse xml
        self._parse_xml_device(xmld, base_url)
        self._parse_xml_service(xmls)

        # Set state
        self.state = 'up'

    def __repr__(self):
        return _s.blue(f'<SSDPService: {_s.reset}{self.id}{_s.blue}>')

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, SSDPService):
            return self.id == other.id

        return False

    # Methods
    def _parse_xml_device(self, xml: ET.Element, base_url: str):
        # Metadata
        self.id = xml.find('upnp:serviceId', XML_DEVICE_NS).text
        self.type = URN(xml.find('upnp:serviceType', XML_DEVICE_NS).text)

        # Urls
        self.scpd = urljoin(base_url, xml.find('upnp:SCPDURL', XML_DEVICE_NS).text)
        self.control = urljoin(base_url, xml.find('upnp:controlURL', XML_DEVICE_NS).text)
        self.event_sub = urljoin(base_url, xml.find('upnp:eventSubURL', XML_DEVICE_NS).text)

    def _parse_xml_service(self, xml: ET.Element):
        # Gather actions
        for child in xml.find('upnp:actionList', XML_SERVICE_NS):
            action = Action(child, self)
            self._actions[action.name] = action

        # Gather state
        for child in xml.find('upnp:serviceStateTable', XML_SERVICE_NS):
            state_var = StateVariable(child, self)
            self._state[state_var.name] = state_var

    async def call(self, action: Union[str, 'Action'], args: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(action, str):
            action = self.action(action)

        # Convert arguments
        soap_args = {}

        for n, v in args.items():
            var = action.argument(n).state_variable
            soap_args[n] = var.type.from_python(v)

        # Request
        async with self._soap as session:
            results = await session.call(self.control, self.type.urn, action.name, soap_args)

        # Convert response
        py_resp = {}

        for n, v in results.items():
            var = action.argument(n).state_variable
            py_resp[n] = var.type.to_python(v)

        return py_resp

    async def subscribe(self, *vars: str, timeout: int = 3600):
        async with self._gena as session:
            await session.subscribe(self.event_sub, *vars, timeout=timeout)

    def update(self, xmld: ET.Element, xmls: ET.Element, base_url: str):
        # Resets
        self._actions = {}
        self._state = {}

        # Parse xml
        self._parse_xml_device(xmld, base_url)
        self._parse_xml_service(xmls)

    def down(self):
        self.state = 'down'

    def action(self, name: str) -> 'Action':
        return self._actions[name]

    def state_variable(self, name: str) -> 'StateVariable':
        return self._state[name]

    def show(self):
        print(f'Service {self.type}')
        print(f'Actions:')
        for action in self.actions:
            print(f'- {action}')

        print()
        print('State:')
        for var in self.state_variables:
            print(f'- {_s_type(var.type)} {var.name}')

    # Properties
    @property
    def actions(self) -> List['Action']:
        return list(self._actions.values())

    @property
    def state_variables(self) -> List['StateVariable']:
        return list(self._state.values())


class Action:
    def __init__(self, xml: ET.Element, service: SSDPService):
        # Attributes
        self.name = xml.find('upnp:name', XML_SERVICE_NS).text
        self._arguments = {}  # type: Dict[str, Argument]

        xal = xml.find('upnp:argumentList', XML_SERVICE_NS)
        if xal is not None:
            for child in xal:
                arg = Argument(child, service)
                self._arguments[arg.name] = arg

        # - internals
        self._service = service

    def __repr__(self):
        return _s.blue(f'<Action: {_s.reset}{self.name}{_s.blue}>')

    def __str__(self):
        parameters = ', '.join(f'{_s_type(arg.type)} {arg.name}' for arg in self.parameters)
        results = ', '.join(f'{_s_type(arg.type)} {arg.name}' for arg in self.parameters)

        return f'{_s.bold(self.name)}({parameters}) -> {results}'

    async def __call__(self, **kwargs):
        return await self.call(**kwargs)

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
        return _s.blue(
            f'<Argument: {_s.green}{self.direction} {_s_type}{self.type} {_s.reset}{self.name}{_s.blue}>'
        )

    def __str__(self):
        return self.name

    # Properties
    @property
    def state_variable(self) -> 'StateVariable':
        return self._service.state_variable(self._state_variable)

    @property
    def type(self) -> SSDPType:
        return self.state_variable.type


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
        self._value = None

    def __repr__(self):
        return _s.blue(
            f'<StateVariable: {_s_type}{self.type} {_s.reset}{self.name}{_s.blue}>'
        )

    # Methods
    async def subscribe(self, timeout: int = 3600):
        await self._service.subscribe(self.name, timeout=timeout)


class ValueRange:
    def __init__(self, xml: ET.Element, stype: SSDPType):
        self.minimum = stype.from_python(xml.find('upnp:minimum', XML_SERVICE_NS).text)
        self.maximum = stype.from_python(xml.find('upnp:maximum', XML_SERVICE_NS).text)

        step = xml_text(xml.find('upnp:step', XML_SERVICE_NS))
        self.step = stype.from_python(step)

    def __repr__(self):
        if self.step is not None:
            return _s.blue(
                f'<ValueRange: {_s.reset}{self.minimum}:{self.maximum}:{self.step}{_s.blue}>'
            )

        return _s.blue(
            f'<ValueRange: {_s.reset}{self.minimum}:{self.maximum}{_s.blue}>'
        )
