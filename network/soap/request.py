from network.utils.xml import add_ns
from typing import Dict
from xml.etree import ElementTree as ET

from .constants import XML_SOAP_NS


# Class
class SOAPRequest:
    def __init__(self, control_url: str, service_type: str, action: str, args: Dict[str, str]):
        # Attributes
        self.control_url = control_url
        self.service_type = service_type
        self.action = action
        self.args = args

    # Methods
    def xml_ns(self) -> Dict[str, str]:
        return {
            **XML_SOAP_NS,
            'upnp': self.service_type
        }

    def headers(self):
        return {
            'Content-Type': 'text/xml; charset="utf-8"',
            'SOAPAction': f'"{self.service_type}#{self.action}"'
        }

    def body(self) -> bytes:
        xml_ns = self.xml_ns()

        root = ET.Element(add_ns('soap:Envelope', xml_ns))
        root.set(add_ns('soap:encodingStyle', xml_ns), 'http://schemas.xmlsoap.org/soap/encoding/')

        body = ET.SubElement(root, add_ns('soap:Body', xml_ns))
        action = ET.SubElement(body, add_ns(f'upnp:{self.action}', xml_ns))

        for n, v in self.args.items():
            arg = ET.SubElement(action, n)
            arg.text = v

        xml = ET.tostring(root, 'utf-8')
        return xml
