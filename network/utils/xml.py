import re

from typing import Dict

# Constants
NS_RE = re.compile(r'^({(?P<ns>[^}]+)})?(?P<tag>.+?)$')


# Utils
def add_ns(tag: str, ns: Dict[str, str]) -> str:
    parts = tag.split(':')

    if len(parts) == 1:
        return tag
    else:
        ns = ns[parts[0]]
        tag = ':'.join(parts[1:])

        return f'{{{ns}}}{tag}'


def strip_ns(tag: str) -> str:
    return NS_RE.match(tag).groupdict()['tag']
