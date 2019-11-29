import re

# Constants
NS_RE = re.compile(r'^({(?P<ns>[^}]+)})?(?P<tag>.+?)$')


# Utils
def strip_ns(tag: str) -> str:
    return NS_RE.match(tag).groupdict()['tag']
