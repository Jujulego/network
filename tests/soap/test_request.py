from network.soap import SOAPRequest
from network.ssdp import URN

# Constants
url = 'http://192.168.1.1:5885/control/'
stype = URN('urn:schemas-upnp-org:service:serviceType:ver')


# Test cases
def test_request_namespaces():
    req = SOAPRequest(url, stype, 'test', {'arg1': '458', 'arg2': '885'})

    # Check namespaces
    ns = req.xml_ns()
    assert ns['soap'] == 'http://schemas.xmlsoap.org/soap/envelope/'
    assert ns['upnp'] == stype


def test_request_headers():
    req = SOAPRequest(url, stype, 'test', {'arg1': '458', 'arg2': '885'})

    # Check headers
    headers = req.headers()
    assert headers['Content-Type'] == 'text/xml; charset="utf-8"'
    assert headers['SOAPAction'] == f'"{stype}#test"'


def test_request_body():
    req = SOAPRequest(url, stype, 'test', {'arg1': '458', 'arg2': '885'})
    result = '<ns0:Envelope xmlns:ns0="http://schemas.xmlsoap.org/soap/envelope/" ns0:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"><ns0:Body><ns1:test xmlns:ns1="urn:schemas-upnp-org:service:serviceType:ver"><ns1:arg1>458</ns1:arg1><ns1:arg2>885</ns1:arg2></ns1:test></ns0:Body></ns0:Envelope>'

    # Check body
    body = req.body()
    assert body == result
