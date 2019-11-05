from typing import Optional, List, Tuple


class SSDPMessage:
    """
    Parse SSDP messages
    """

    def __init__(self, message: str, sender: Optional[Tuple[str, int]] = None):
        self._parse_message(message)
        self.sender = sender

    def __repr__(self):
        if self.sender is not None:
            return "<ssdp.SSDPMessage: {0} from {1[0]}:{1[1]}>".format(self.method, self.sender)

        return "<ssdp.SSDPMessage: {}>".format(self.method)

    # Methods
    def _parse_message(self, message):
        lines = message.splitlines()

        self._parse_request(lines[0])
        self._parse_headers(lines[1:])

    def _parse_request(self, request: str):
        rq = request.split(' ')

        self.method = rq[0]
        self.http_version = rq[2]

    def _parse_headers(self, headers: List[str]):
        self.headers = {}

        for header in headers:
            dp = header.find(':')
            self.headers[header[:dp].upper()] = header[dp+1:].strip()

    # Properties
    @property
    def host(self) -> Optional[Tuple[str, int]]:
        host = self.headers.get('HOST')

        if host is None:
            return None

        parts = host.split(':')
        if len(parts) == 1:
            return parts[0], 1900

        return parts[0], int(parts[0])

    # - NOTIFY headers
    @property
    def location(self) -> Optional[str]:
        return self.headers.get('LOCATION')

    @property
    def nt(self) -> Optional[str]:
        return self.headers.get('NT')

    @property
    def nts(self) -> Optional[str]:
        return self.headers.get('NTS')

    # - M-SEARCH headers
    @property
    def man(self) -> Optional[str]:
        return self.headers.get('MAN')

    @property
    def mx(self) -> Optional[str]:
        return self.headers.get('MX')

    @property
    def st(self) -> Optional[str]:
        return self.headers.get('ST')
