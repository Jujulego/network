# Class
class SSDPType:
    # Methods
    def to_python(self, val: str):
        return val

    def from_python(self, val) -> str:
        return str(val)


class SSDPBool(SSDPType):
    # Methods
    def to_python(self, val: str) -> bool:
        return val in ('1', 'true', 'yes')

    def from_python(self, val: bool) -> str:
        return '1' if val else '0'


class SSDPInt(SSDPType):
    # Methods
    def to_python(self, val: str) -> int:
        return int(val)


class SSDPFloat(SSDPType):
    # Methods
    def to_python(self, val: str) -> float:
        return float(val)


# Utils
def get_type(name: str) -> SSDPType:
    if name in ('ui1', 'ui2', 'ui4', 'ui8', 'i1', 'i2', 'i4', 'i8', 'int'):
        return SSDPInt()

    elif name in ('r4', 'r8', 'number', 'fixed.14.4', 'float', 'number'):
        return SSDPFloat()

    return SSDPType()
