# Class
class URN:
    def __init__(self, urn: str):
        # Check
        parts = urn.split(':')

        if parts[0] == 'urn' and len(parts) != 5:
            raise ValueError(f'Invalid URN : {urn}')

        # Get parts
        self.domain = parts[1]
        self.kind = parts[2]
        self.type = parts[3]
        self.version = parts[4]

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
