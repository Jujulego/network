import re

# Constants
URN_RE = re.compile(r'^urn:(?P<domain>[^:]+):(?P<kind>(device)|(service)):(?P<type>[^:]+):(?P<version>[^:]+)$', re.I)


# Class
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
