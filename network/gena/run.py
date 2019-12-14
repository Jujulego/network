from .server import GENAServer
from .session import GENASession

__all__ = ['get_gena_server', 'get_gena_session']

# Constants
running_server = GENAServer()


# Utils
def get_gena_server() -> GENAServer:
    return running_server


def get_gena_session() -> GENASession:
    return running_server.get_session()
