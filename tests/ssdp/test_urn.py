import pytest

from network.ssdp import URN


# Test cases
def test_urn_logics():
    urn_dev1 = URN('urn:schemas-upnp-org:device:deviceType:ver')
    urn_dev2 = URN('urn:schemas-upnp-org:device:deviceType:ver')
    urn_serv = URN('urn:schemas-upnp-org:service:serviceType:ver')

    # Check __eq__
    assert (urn_dev1 == urn_dev2) is True
    assert (urn_dev1 == urn_serv) is False

    assert (urn_dev1 == 'urn:schemas-upnp-org:device:deviceType:ver') is True
    assert (urn_dev1 == 'urn:schemas-upnp-org:service:serviceType:ver') is False

    assert (urn_dev1 == object()) is False


def test_urn_hash():
    urn_dev1 = URN('urn:schemas-upnp-org:device:deviceType:ver')
    urn_dev2 = URN('urn:schemas-upnp-org:device:deviceType:ver')
    urn_serv = URN('urn:schemas-upnp-org:service:serviceType:ver')

    # Check __hash__
    assert hash(urn_dev1) == hash(urn_dev2)
    assert hash(urn_dev1) != hash(urn_serv)

    assert hash(urn_dev1) == hash('urn:schemas-upnp-org:device:deviceType:ver')
    assert hash(urn_dev1) != hash('urn:schemas-upnp-org:service:serviceType:ver')


def test_upnp_urn():
    urn = URN('urn:schemas-upnp-org:device:deviceType:ver')

    # Check decomposition
    assert urn.domain == 'schemas-upnp-org'
    assert urn.is_vendor is False
    assert urn.kind == 'device'
    assert urn.type == 'deviceType'
    assert urn.version == 'ver'

    # Check reconstruction
    assert urn.urn == 'urn:schemas-upnp-org:device:deviceType:ver'
    assert str(urn) == 'urn:schemas-upnp-org:device:deviceType:ver'


def test_vendor_urn():
    urn = URN('urn:domain-name:service:serviceType:ver')

    # Check decomposition
    assert urn.domain == 'domain-name'
    assert urn.is_vendor is True
    assert urn.kind == 'service'
    assert urn.type == 'serviceType'
    assert urn.version == 'ver'

    # Check reconstruction
    assert urn.urn == 'urn:domain-name:service:serviceType:ver'
    assert str(urn) == 'urn:domain-name:service:serviceType:ver'


def test_falsy_urn():
    with pytest.raises(ValueError):
        URN("falsy_urn")
