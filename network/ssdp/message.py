from network.typing import Address
from typing import Optional, Union, Dict, List

from .usn import USN
from .urn import URN

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
            self.method = None if is_response else method
            self.http_version = "HTTP/1.1"

            self.headers = headers
            if not is_response and 'HOST' not in self.headers:
                self.headers['HOST'] = "239.255.255.250:1900"

    def __repr__(self):
        return "<ssdp.SSDPMessage: {}>".format(self.method or "RESPONSE")

    # Methods
    def _parse_message(self, message):
        lines = message.splitlines()

        self._parse_request(lines[0])
        self._parse_headers(lines[1:])

    def _parse_request(self, request: str):
        rq = request.split(' ')

        if rq[0] == 'HTTP/1.1':
            self.is_response = True
            self.method = None
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
        return '\r\n'.join([self._gen_request(), *self._gen_headers()]) + '\r\n' * 2

    def _gen_request(self) -> str:
        return f'{self.http_version} 200 OK' if self.is_response else f'{self.method} * {self.http_version}'

    def _gen_headers(self) -> List[str]:
        return [f'{n}: {v}' for n, v in self.headers.items()]

    # Properties
    @property
    def message(self) -> str:
        return self._gen_message()

    @property
    def host(self) -> Optional[Address]:
        host = self.headers.get('HOST')

        if host is None:
            return None

        parts = host.split(':')
        if len(parts) == 1:
            return parts[0], 1900

        return parts[0], int(parts[1])

    # - NOTIFY headers
    @property
    def max_age(self) -> Optional[int]:
        if 'CACHE-CONTROL' not in self.headers:
            return None

        return int(self.headers['CACHE-CONTROL'].split('=')[1])

    @max_age.setter
    def max_age(self, age: int):
        self.headers['CACHE-CONTROL'] = f'max-age={age}'

    @property
    def location(self) -> Optional[str]:
        return self.headers.get('LOCATION')

    @location.setter
    def location(self, location: str):
        self.headers['LOCATION'] = location

    @property
    def nt(self) -> Union[URN, str, None]:
        nt = self.headers.get('NT')

        if nt is not None and nt.startswith('urn'):
            nt = URN(nt)

        return nt

    @nt.setter
    def nt(self, nt: Union[URN, str]):
        if isinstance(nt, URN):
            nt = nt.urn

        self.headers['NT'] = nt

    @property
    def nts(self) -> Optional[str]:
        return self.headers.get('NTS')

    @nts.setter
    def nts(self, nts: str):
        self.headers['NTS'] = nts

    @property
    def usn(self) -> Optional[USN]:
        return USN(self.headers['USN']) if 'USN' in self.headers else None

    @usn.setter
    def usn(self, usn: Union[str, USN]):
        if isinstance(usn, USN):
            usn = str(usn)

        self.headers['USN'] = usn

    # - M-SEARCH headers
    @property
    def man(self) -> Optional[str]:
        return self.headers.get('MAN')

    @man.setter
    def man(self, man: str):
        self.headers['MAN'] = man

    @property
    def mx(self) -> Optional[int]:
        mx = self.headers.get('MX')

        return None if mx is None else int(mx)

    @mx.setter
    def mx(self, mx: int):
        self.headers['MX'] = str(mx)

    @property
    def st(self) -> Union[URN, str, None]:
        st = self.headers.get('ST')

        if st is not None and st.startswith('urn'):
            st = URN(st)

        return st

    @st.setter
    def st(self, st: Union[URN, str]):
        if isinstance(st, URN):
            st = st.urn

        self.headers['ST'] = st
