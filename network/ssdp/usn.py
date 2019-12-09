import re

from typing import Any

from .urn import URN

# Constants
USN_RE = re.compile(r'^uuid:(?P<uuid>[^:]+)(::((?P<root>upnp:rootdevice)|(?P<urn>urn:.+)))?$', re.I)


# Class
class USN:
    def __init__(self, usn: str):
        # Parse string
        parts = USN_RE.match(usn)

        if parts is None:
            raise ValueError(f'Invalid USN : {usn}')

        # Get parts
        parts = parts.groupdict()

        self.uuid = parts['uuid'].lower()
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

    def __hash__(self):
        return hash(self.usn)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, USN):
            other = other.usn

        if isinstance(other, str):
            return self.usn == other

        return False

    # Property
    @property
    def usn(self):
        if self.is_root:
            return f'uuid:{self.uuid}::upnp:rootdevice'

        elif self.urn is not None:
            return f'uuid:{self.uuid}::{self.urn}'

        return f'uuid:{self.uuid}'
