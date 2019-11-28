import unittest

from network.ssdp import URN, USN


# Test cases
class URNTestCase(unittest.TestCase):
    # Tests
    def test_urn_logics(self):
        urn_dev1 = URN('urn:schemas-upnp-org:device:deviceType:ver')
        urn_dev2 = URN('urn:schemas-upnp-org:device:deviceType:ver')
        urn_serv = URN('urn:schemas-upnp-org:service:serviceType:ver')

        # Check __eq__
        self.assertEqual(urn_dev1 == urn_dev2, True)
        self.assertEqual(urn_dev1 == urn_serv, False)

        self.assertEqual(urn_dev1 == 'urn:schemas-upnp-org:device:deviceType:ver', True)
        self.assertEqual(urn_dev1 == 'urn:schemas-upnp-org:service:serviceType:ver', False)

        self.assertEqual(urn_dev1 == object(), False)

        # Check __ne__
        self.assertEqual(urn_dev1 != urn_dev2, False)
        self.assertEqual(urn_dev1 != urn_serv, True)

        self.assertEqual(urn_dev1 != 'urn:schemas-upnp-org:device:deviceType:ver', False)
        self.assertEqual(urn_dev1 != 'urn:schemas-upnp-org:service:serviceType:ver', True)

        self.assertEqual(urn_dev1 != object(), True)

    def test_urn_hash(self):
        urn_dev1 = URN('urn:schemas-upnp-org:device:deviceType:ver')
        urn_dev2 = URN('urn:schemas-upnp-org:device:deviceType:ver')
        urn_serv = URN('urn:schemas-upnp-org:service:serviceType:ver')

        # Check __hash__
        self.assertEqual(hash(urn_dev1), hash(urn_dev2))
        self.assertNotEqual(hash(urn_dev1), hash(urn_serv))

        self.assertEqual(hash(urn_dev1), hash('urn:schemas-upnp-org:device:deviceType:ver'))
        self.assertNotEqual(hash(urn_dev1), hash('urn:schemas-upnp-org:service:serviceType:ver'))

    def test_upnp_urn(self):
        urn = URN('urn:schemas-upnp-org:device:deviceType:ver')

        # Check decomposition
        self.assertEqual(urn.domain, 'schemas-upnp-org')
        self.assertEqual(urn.is_vendor, False)
        self.assertEqual(urn.kind, 'device')
        self.assertEqual(urn.type, 'deviceType')
        self.assertEqual(urn.version, 'ver')

        # Check reconstruction
        self.assertEqual(urn.urn, 'urn:schemas-upnp-org:device:deviceType:ver')
        self.assertEqual(str(urn), 'urn:schemas-upnp-org:device:deviceType:ver')

    def test_vendor_urn(self):
        urn = URN('urn:domain-name:service:serviceType:ver')

        # Check decomposition
        self.assertEqual(urn.domain, 'domain-name')
        self.assertEqual(urn.is_vendor, True)
        self.assertEqual(urn.kind, 'service')
        self.assertEqual(urn.type, 'serviceType')
        self.assertEqual(urn.version, 'ver')

        # Check reconstruction
        self.assertEqual(urn.urn, 'urn:domain-name:service:serviceType:ver')
        self.assertEqual(str(urn), 'urn:domain-name:service:serviceType:ver')

    def test_falsy_urn(self):
        with self.assertRaises(ValueError):
            URN("falsy_urn")


class USNTestCase(unittest.TestCase):
    # Tests
    def test_usn_logics(self):
        usn = USN('uuid:device-UUID')
        usn_eq = USN('uuid:device-UUID')
        usn_ne = USN('uuid:other-device-UUID')

        # Check __eq__
        self.assertEqual(usn == usn_eq, True)
        self.assertEqual(usn == usn_ne, False)

        self.assertEqual(usn == 'uuid:device-UUID', True)
        self.assertEqual(usn == 'uuid:other-device-UUID', False)

        self.assertEqual(usn == object(), False)

        # Check __ne__
        self.assertEqual(usn != usn_eq, False)
        self.assertEqual(usn != usn_ne, True)

        self.assertEqual(usn != 'uuid:device-UUID', False)
        self.assertEqual(usn != 'uuid:other-device-UUID', True)

        self.assertEqual(usn != object(), True)

    def test_usn_hash(self):
        usn = USN('uuid:device-UUID')
        usn_eq = USN('uuid:device-UUID')
        usn_ne = USN('uuid:other-device-UUID')

        # Check __hash__
        self.assertEqual(hash(usn), hash(usn_eq))
        self.assertNotEqual(hash(usn), hash(usn_ne))

        self.assertEqual(hash(usn), hash('uuid:device-UUID'))
        self.assertNotEqual(hash(usn), hash('uuid:other-device-UUID'))

    def test_uuid_usn(self):
        usn = USN('uuid:device-UUID')

        # Check decomposition
        self.assertEqual(usn.uuid, 'device-UUID')
        self.assertEqual(usn.is_root, False)
        self.assertIsNone(usn.urn)

        # Check reconstruction
        self.assertEqual(usn.usn, 'uuid:device-UUID')
        self.assertEqual(str(usn), 'uuid:device-UUID')

    def test_root_usn(self):
        usn = USN('uuid:device-UUID::upnp:rootdevice')

        # Check decomposition
        self.assertEqual(usn.uuid, 'device-UUID')
        self.assertEqual(usn.is_root, True)
        self.assertIsNone(usn.urn)

        # Check reconstruction
        self.assertEqual(usn.usn, 'uuid:device-UUID::upnp:rootdevice')
        self.assertEqual(str(usn), 'uuid:device-UUID::upnp:rootdevice')

    def test_urn_usn(self):
        usn = USN('uuid:device-UUID::urn:schemas-upnp-org:device:deviceType:ver')

        # Check decomposition
        self.assertEqual(usn.uuid, 'device-UUID')
        self.assertEqual(usn.is_root, False)
        self.assertIsInstance(usn.urn, URN)
        self.assertEqual(usn.urn, 'urn:schemas-upnp-org:device:deviceType:ver')

        # Check reconstruction
        self.assertEqual(usn.usn, 'uuid:device-UUID::urn:schemas-upnp-org:device:deviceType:ver')
        self.assertEqual(str(usn), 'uuid:device-UUID::urn:schemas-upnp-org:device:deviceType:ver')

    def test_falsy_usn(self):
        with self.assertRaises(ValueError):
            USN("falsy_usn")
