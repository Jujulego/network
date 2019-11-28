import pytest

from network.ssdp import URN, USN


# Test cases
def test_usn_logics():
    usn = USN('uuid:device-UUID')
    usn_eq = USN('uuid:device-UUID')
    usn_ne = USN('uuid:other-device-UUID')

    # Check __eq__
    assert (usn == usn_eq) is True
    assert (usn == usn_ne) is False

    assert (usn == 'uuid:device-UUID') is True
    assert (usn == 'uuid:other-device-UUID') is False

    assert (usn == object()) is False


def test_usn_hash():
    usn = USN('uuid:device-UUID')
    usn_eq = USN('uuid:device-UUID')
    usn_ne = USN('uuid:other-device-UUID')

    # Check __hash__
    assert hash(usn) == hash(usn_eq)
    assert hash(usn) != hash(usn_ne)

    assert hash(usn) == hash('uuid:device-UUID')
    assert hash(usn) != hash('uuid:other-device-UUID')


def test_uuid_usn():
    usn = USN('uuid:device-UUID')

    # Check decomposition
    assert usn.uuid == 'device-UUID'
    assert usn.is_root is False
    assert usn.urn is None

    # Check reconstruction
    assert usn.usn == 'uuid:device-UUID'
    assert str(usn) == 'uuid:device-UUID'


def test_root_usn():
    usn = USN('uuid:device-UUID::upnp:rootdevice')

    # Check decomposition
    assert usn.uuid == 'device-UUID'
    assert usn.is_root is True
    assert usn.urn is None

    # Check reconstruction
    assert usn.usn == 'uuid:device-UUID::upnp:rootdevice'
    assert str(usn) == 'uuid:device-UUID::upnp:rootdevice'


def test_urn_usn():
    usn = USN('uuid:device-UUID::urn:schemas-upnp-org:device:deviceType:ver')

    # Check decomposition
    assert usn.uuid == 'device-UUID'
    assert usn.is_root is False
    assert isinstance(usn.urn, URN)
    assert usn.urn == 'urn:schemas-upnp-org:device:deviceType:ver'

    # Check reconstruction
    assert usn.usn == 'uuid:device-UUID::urn:schemas-upnp-org:device:deviceType:ver'
    assert str(usn) == 'uuid:device-UUID::urn:schemas-upnp-org:device:deviceType:ver'


def test_falsy_usn():
    with pytest.raises(ValueError):
        USN("falsy_usn")
