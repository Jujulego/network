from network.soap import SOAPResponse
from network.ssdp.urn import URN

# Constants
stype = URN('urn:schemas-upnp-org:service:serviceType:ver')
action = 'test'

xml = (
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    '  <s:Body>'
   f'    <u:{action}Response xmlns:u="{stype}">'
    '      <arg1>458</arg1>'
    '      <arg2>885</arg2>'
   f'    </u:{action}Response>'
    '  </s:Body>'
    '</s:Envelope>'
)
xml_error = (
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/" s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
    '  <s:Body>'
    '    <s:Fault>'
    '      <faultcode>s:Client</faultcode>'
    '      <faultstring>UPnPError</faultstring>'
    '      <detail>'
    '        <UPnPError xmlns="urn:schemas-upnp-org:control-1-0">'
    '          <errorCode>885</errorCode>'
    '          <errorDescription>error string</errorDescription>'
    '        </UPnPError>'
    '      </detail>'
    '    </s:Fault>'
    '  </s:Body>'
    '</s:Envelope>'
)


# Test cases
def test_response_namespaces():
    res = SOAPResponse(stype.urn, action, xml)

    # Check namespaces
    ns = res.xml_ns()
    assert ns['soap'] == 'http://schemas.xmlsoap.org/soap/envelope/'
    assert ns['control'] == 'urn:schemas-upnp-org:control-1-0'
    assert ns['upnp'] == stype


def test_response_args():
    res = SOAPResponse(stype.urn, action, xml)

    # Check args
    assert 'arg1' in res.results and res.results['arg1'] == '458'
    assert 'arg2' in res.results and res.results['arg2'] == '885'


def test_response_error():
    res = SOAPResponse(stype.urn, action, xml_error, is_error=True)

    # Check args
    assert res.fault_code == 's:Client'
    assert res.fault_string == 'UPnPError'
    assert res.error_code == 885
    assert res.error_description == 'error string'
