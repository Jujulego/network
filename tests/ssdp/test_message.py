from network.ssdp import SSDPMessage, USN, URN

# Constants
uuid = 'device-uuid'

urn = 'urn:schemas-upnp-org:device:deviceType:ver'
usn = f'uuid:{uuid}::{urn}'


# Utils
def notify_alive_msg(nt: str) -> str:
    return f'NOTIFY * HTTP/1.1\r\n' \
           f'HOST: 239.255.255.250:1900\r\n' \
           f'CACHE-CONTROL: max-age=900\r\n' \
           f'LOCATION: http://example.com/\r\n' \
           f'NT: {nt}\r\n' \
           f'NTS: ssdp:alive\r\n' \
           f'SERVER: OS/version UPnP/2.0 product/version\r\n' \
           f'USN: {usn}\r\n' \
           f'BOOTID.UPNP.ORG: 5557\r\n' \
           f'CONFIGID.UPNP.ORG: 155665\r\n' \
           f'SEARCHPORT.UPNP.ORG: 55254\r\n' \
           f'\r\n' \
           f''


def notify_byebye_msg(nt: str) -> str:
    return f'NOTIFY * HTTP/1.1\r\n' \
           f'HOST: 239.255.255.250:1900\r\n' \
           f'NT: {nt}\r\n' \
           f'NTS: ssdp:byebye\r\n' \
           f'USN: {usn}\r\n' \
           f'BOOTID.UPNP.ORG: 5557\r\n' \
           f'CONFIGID.UPNP.ORG: 155665\r\n' \
           f'\r\n' \
           f''


def msearch_msg(st: str) -> str:
    return f'MSEARCH * HTTP/1.1\r\n' \
           f'HOST: 239.255.255.250:1900\r\n' \
           f'MAN: "ssdp:discover"\r\n' \
           f'MX: 5\r\n' \
           f'ST: {st}\r\n' \
           f'USER-AGENT: OS/version UPnP/2.0 product/version\r\n' \
           f'BOOTID.UPNP.ORG: 5557\r\n' \
           f'CONFIGID.UPNP.ORG: 155665\r\n' \
           f'\r\n' \
           f''


def msearch_response_msg(st: str) -> str:
    return f'HTTP/1.1 200 OK\r\n' \
           f'CACHE-CONTROL: max-age=900\r\n' \
           f'EXT: \r\n' \
           f'LOCATION: http://example.com/\r\n' \
           f'SERVER: OS/version UPnP/2.0 product/version\r\n' \
           f'ST: {st}\r\n' \
           f'USN: {usn}\r\n' \
           f'BOOTID.UPNP.ORG: 5557\r\n' \
           f'CONFIGID.UPNP.ORG: 155665\r\n' \
           f'SEARCHPORT.UPNP.ORG: 55254\r\n' \
           f'\r\n' \
           f''


# Test cases
def test_notify_alive_parse():
    msg = SSDPMessage(message=notify_alive_msg('upnp:rootdevice'))

    # Check message kind
    assert msg.is_response is False
    assert msg.method == 'NOTIFY'
    assert msg.http_version == 'HTTP/1.1'

    # Check message headers
    assert msg.host == ('239.255.255.250', 1900)
    assert msg.max_age == 900
    assert msg.location == 'http://example.com/'
    assert isinstance(msg.nt, str)
    assert msg.nt == 'upnp:rootdevice'
    assert msg.nts == 'ssdp:alive'
    assert isinstance(msg.usn, USN)
    assert msg.usn == usn
    assert msg.man is None
    assert msg.mx is None
    assert msg.st is None
    assert msg.headers['SERVER'] == 'OS/version UPnP/2.0 product/version'
    assert msg.headers['BOOTID.UPNP.ORG'] == '5557'
    assert msg.headers['CONFIGID.UPNP.ORG'] == '155665'
    assert msg.headers['SEARCHPORT.UPNP.ORG'] == '55254'

    # Check with nt == urn
    msg = SSDPMessage(message=notify_alive_msg(urn))

    assert isinstance(msg.nt, URN)
    assert msg.nt == urn


def test_notify_byebye_parse():
    msg = SSDPMessage(message=notify_byebye_msg('upnp:rootdevice'))

    # Check message kind
    assert msg.is_response is False
    assert msg.method == 'NOTIFY'
    assert msg.http_version == 'HTTP/1.1'

    # Check message headers
    assert msg.host == ('239.255.255.250', 1900)
    assert msg.max_age is None
    assert msg.location is None
    assert isinstance(msg.nt, str)
    assert msg.nt == 'upnp:rootdevice'
    assert msg.nts == 'ssdp:byebye'
    assert isinstance(msg.usn, USN)
    assert msg.usn == usn
    assert msg.man is None
    assert msg.mx is None
    assert msg.st is None
    assert msg.headers['BOOTID.UPNP.ORG'] == '5557'
    assert msg.headers['CONFIGID.UPNP.ORG'] == '155665'

    # Check with nt == urn
    msg = SSDPMessage(message=notify_byebye_msg(urn))

    assert isinstance(msg.nt, URN)
    assert msg.nt == urn


def test_msearch_parse():
    msg = SSDPMessage(message=msearch_msg('ssdp:all'))

    # Check message kind
    assert msg.is_response is False
    assert msg.method == 'MSEARCH'
    assert msg.http_version == 'HTTP/1.1'

    # Check message headers
    assert msg.host == ('239.255.255.250', 1900)
    assert msg.max_age is None
    assert msg.location is None
    assert msg.nt is None
    assert msg.nts is None
    assert msg.usn is None
    assert msg.man == '"ssdp:discover"'
    assert msg.mx == 5
    assert isinstance(msg.st, str)
    assert msg.st == 'ssdp:all'
    assert msg.headers['USER-AGENT'] == 'OS/version UPnP/2.0 product/version'
    assert msg.headers['BOOTID.UPNP.ORG'] == '5557'
    assert msg.headers['CONFIGID.UPNP.ORG'] == '155665'

    # Check with st == urn
    msg = SSDPMessage(message=msearch_msg(urn))

    assert isinstance(msg.st, URN)
    assert msg.st == urn


def test_msearch_response_parse():
    msg = SSDPMessage(message=msearch_response_msg('ssdp:all'))

    # Check message kind
    assert msg.is_response is True
    assert msg.method is None
    assert msg.http_version == 'HTTP/1.1'

    # Check message headers
    assert msg.host is None
    assert msg.max_age == 900
    assert msg.location == 'http://example.com/'
    assert msg.nt is None
    assert msg.nts is None
    assert isinstance(msg.usn, USN)
    assert msg.usn == usn
    assert msg.man is None
    assert msg.mx is None
    assert isinstance(msg.st, str)
    assert msg.st == 'ssdp:all'
    assert msg.headers['SERVER'] == 'OS/version UPnP/2.0 product/version'
    assert msg.headers['BOOTID.UPNP.ORG'] == '5557'
    assert msg.headers['CONFIGID.UPNP.ORG'] == '155665'
    assert msg.headers['SEARCHPORT.UPNP.ORG'] == '55254'

    # Check with st == urn
    msg = SSDPMessage(message=msearch_response_msg(urn))

    assert isinstance(msg.st, URN)
    assert msg.st == urn


def test_request_generate():
    msg = SSDPMessage(
        method='NOTIFY',
        headers={
            'HOST': '239.255.255.250:1900',
            'CACHE-CONTROL': 'max-age=900',
            'LOCATION': 'http://example.com/',
            'NT': 'upnp:rootdevice',
            'NTS': 'ssdp:alive',
            'SERVER': 'OS/version UPnP/2.0 product/version',
            'USN': usn,
            'BOOTID.UPNP.ORG': '5557',
            'CONFIGID.UPNP.ORG': '155665',
            'SEARCHPORT.UPNP.ORG': '55254'
        }
    )

    # Check message kind
    assert msg.message == notify_alive_msg('upnp:rootdevice')


def test_response_generate():
    msg = SSDPMessage(
        is_response=True,
        headers={
            'CACHE-CONTROL': 'max-age=900',
            'EXT': '',
            'LOCATION': 'http://example.com/',
            'SERVER': 'OS/version UPnP/2.0 product/version',
            'ST': 'upnp:rootdevice',
            'USN': usn,
            'BOOTID.UPNP.ORG': '5557',
            'CONFIGID.UPNP.ORG': '155665',
            'SEARCHPORT.UPNP.ORG': '55254'
        }
    )

    # Check message kind
    assert msg.message == msearch_response_msg('upnp:rootdevice')
