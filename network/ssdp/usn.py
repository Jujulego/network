import re

# Constants
USN_RE = re.compile(r'^uuid:(?P<uuid>[^:]+)(::((?P<root>upnp:rootdevice)|(?P<urn>urn:.+)))?$', re.I)
URN_RE = re.compile(r'^urn:(?P<domain>[^:]+):(?P<kind>(device)|(service)):(?P<type>[^:]+):(?P<version>[^:]+)$', re.I)


# Class
class USN:
    def __init__(self, usn: str):
        # Parse string
        parts = USN_RE.match(usn)

        if parts is None:
            raise ValueError(f'Invalid USN : {usn}')

        # Get parts
        parts = parts.groupdict()

        self.uuid = parts['uuid']
        self.is_root = parts['root'] is not None
        self.urn = URN(parts['urn']) if parts['urn'] is not None else None

    def __repr__(self):
        if self.is_root:
            return f'<USN: {self.uuid} (root)>'

        elif self.urn is not None:
            return f'<USN: {self.uuid} (urn)>'

        return f'<USN: {self.uuid}>'

    def __str__(self) -> str:
        return self.usn

    # Property
    @property
    def usn(self):
        if self.is_root:
            return f'uuid:{self.uuid}::upnp:rootdevice'

        elif self.urn is not None:
            return f'uuid:{self.uuid}:{self.urn}'

        return f'uuid:{self.uuid}'


class URN:
    def __init__(self, urn: str):
        # Parse string
        parts = URN_RE.match(urn)

        if parts is None:
            raise ValueError(f'Invalid URN : {urn}')

        # Get parts
        parts = parts.groupdict()

        self.domain = parts['domain']
        self.kind = parts['kind']
        self.type = parts['type']
        self.version = parts['version']

    def __repr__(self):
        if self.is_vendor:
            return f'<URN: {self.kind} {self.domain} {self.type} ({self.version})>'

        return f'<URN: {self.kind} {self.type} ({self.version})>'

    def __str__(self) -> str:
        return self.urn

    # Property
    @property
    def is_vendor(self) -> bool:
        return self.domain != 'schemas-upnp-org'

    @property
    def urn(self):
        return f'urn:{self.domain}:{self.kind}:{self.type}:{self.version}'
