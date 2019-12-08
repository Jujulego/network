import asyncio

from functools import wraps
from typing import Any, Callable, Optional


# Decorators
def with_loop(default: Optional[Callable[[], asyncio.AbstractEventLoop]] = None):
    if default is None:
        default = asyncio.get_event_loop

    def deco(fun: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(fun)
        def f(*args, loop: Optional[asyncio.AbstractEventLoop] = None, **kwargs):
            if loop is None:
                loop = default()

            return fun(*args, loop=loop, **kwargs)

        return f
    return deco


def with_event_loop(fun: Callable[..., Any]) -> Callable[..., Any]:
    return with_loop()(fun)
