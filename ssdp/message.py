from typing import Optional, Dict, List, Tuple

Headers = Dict[str, str]


class SSDPMessage:
    """
    Parse SSDP messages
    """

    def __init__(
            self, *,
            message: Optional[str] = None,
            method: Optional[str] = None, is_response: bool = False, headers: Optional[Headers] = None
    ):
        if message is not None:
            self._parse_message(message)
        else:
            self.is_response = is_response
            self.method = "" if is_response else method

            self.headers = headers
            if not self.headers.has('HOST'):
                self.headers['HOST'] = "239.255.255.250:1900"

    def __repr__(self):
        return "<ssdp.SSDPMessage: {}>".format(self.method)

    # Methods
    def _parse_message(self, message):
        lines = message.splitlines()

        self._parse_request(lines[0])
        self._parse_headers(lines[1:])

    def _parse_request(self, request: str):
        rq = request.split(' ')

        if rq[0] == 'HTTP/1.1':
            self.is_response = True
            self.http_version = rq[0]

        else:
            self.is_response = False
            self.method = rq[0]
            self.http_version = rq[2]

    def _parse_headers(self, headers: List[str]):
        self.headers = {}

        for header in headers:
            dp = header.find(':')
            self.headers[header[:dp].upper()] = header[dp+1:].strip()

    def _gen_message(self) -> str:
        return '\r\n'.join([self._gen_request(), *self._gen_headers()])

    def _gen_request(self) -> str:
        return (
            "{0[http_version]} 200 OK" if self.is_response else "{0[method]} * {0[http_version]}"
        ).format(self)

    def _gen_headers(self) -> List[str]:
        return ['{}: {}'.format(n, v) for n, v in self.headers.items()]

    # Properties
    @property
    def message(self) -> str:
        return self._gen_message()

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

    @location.setter
    def location(self, location: str):
        self.headers['LOCATION'] = location

    @property
    def nt(self) -> Optional[str]:
        return self.headers.get('NT')

    @nt.setter
    def nt(self, nt: str):
        self.headers['NT'] = nt

    @property
    def nts(self) -> Optional[str]:
        return self.headers.get('NTS')

    @nts.setter
    def nts(self, nts: str):
        self.headers['NTS'] = nts

    # - M-SEARCH headers
    @property
    def man(self) -> Optional[str]:
        return self.headers.get('MAN')

    @man.setter
    def man(self, man: str):
        self.headers['MAN'] = man

    @property
    def mx(self) -> Optional[str]:
        return self.headers.get('MX')

    @mx.setter
    def mx(self, mx: str):
        self.headers['MX'] = mx

    @property
    def st(self) -> Optional[str]:
        return self.headers.get('ST')

    @st.setter
    def st(self, st: str):
        self.headers['ST'] = st
