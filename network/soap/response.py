from typing import Dict
from xml.etree import ElementTree as ET

from .constants import XML_SOAP_NS


# Class
class SOAPResponse:
    def __init__(self, service_type: str, action: str, data: str, is_error: bool = False):
        # Attributes
        self.is_error = is_error
        self.service_type = service_type
        self.action = action

        self._parse_data(data)

    # Methods
    def xml_ns(self) -> Dict[str, str]:
        return {
            **XML_SOAP_NS,
            'upnp': self.service_type
        }

    def _parse_data(self, data: str):
        xml_ns = self.xml_ns()
        xml = ET.fromstring(data)

        body = xml.find('soap:Body', xml_ns)

        if self.is_error:
            self._parse_error(body)
        else:
            self._parse_response(body)

    def _parse_error(self, xml: ET.Element):
        xml_ns = self.xml_ns()
        fault = xml.find('soap:Fault', xml_ns)

        # fault data (fixed by UPnP)
        self.fault_code = fault.find('faultcode').text
        self.fault_string = fault.find('faultstring').text

        # error data
        detail = fault.find('detail')
        err = detail.find('control:UPnPError', xml_ns)

        self.error_code = int(err.find('control:errorCode', xml_ns).text)
        self.error_description = err.find('control:errorDescription', xml_ns).text

    def _parse_response(self, xml: ET.Element):
        xml_ns = self.xml_ns()
        rep = xml.find(f'upnp:{self.action}Response', xml_ns)

        # Get out arguments
        self.results = {arg.tag: arg.text for arg in rep}
