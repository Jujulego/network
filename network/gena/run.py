from .server import GENAServer
from .session import GENASession

__all__ = ['get_gena_server', 'get_gena_session']

# Constants
_server = GENAServer()


# Utils
def get_gena_server() -> GENAServer:
    return _server


def get_gena_session() -> GENASession:
    return _server.get_session()
