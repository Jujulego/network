from network.soap import SOAPRequest
from network.ssdp.urn import URN

# Constants
url = 'http://192.168.1.1:5885/control/'
stype = URN('urn:schemas-upnp-org:service:serviceType:ver')

xml = (
    '<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns1="urn:schemas-upnp-org:service:serviceType:ver" ns0:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">'
      '<ns0:Body>'
        '<ns1:test>'
          '<arg1>458</arg1>'
          '<arg2>885</arg2>'
        '</ns1:test>'
      '</ns0:Body>'
    '</ns0:Envelope>'
).encode('utf-8')


# Test cases
def test_request_namespaces():
    req = SOAPRequest(url, stype.urn, 'test', {'arg1': '458', 'arg2': '885'})

    # Check namespaces
    ns = req.xml_ns()
    assert ns['soap'] == 'http://schemas.xmlsoap.org/soap/envelope/'
    assert ns['control'] == 'urn:schemas-upnp-org:control-1-0'
    assert ns['upnp'] == stype


def test_request_headers():
    req = SOAPRequest(url, stype.urn, 'test', {'arg1': '458', 'arg2': '885'})

    # Check headers
    headers = req.headers()
    assert headers['Content-Type'] == 'text/xml; charset="utf-8"'
    assert headers['SOAPAction'] == f'"{stype}#test"'


def test_request_body():
    req = SOAPRequest(url, stype.urn, 'test', {'arg1': '458', 'arg2': '885'})

    # Check body
    body = req.body()
    assert body == xml
