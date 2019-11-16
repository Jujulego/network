import aioconsole
import argparse
import asyncio

from abc import ABC
from typing import Optional, Callable, Dict, Tuple


# Utils
def is_command(obj) -> bool:
    return hasattr(obj, '__is_command__') and obj.__is_command__


# Class
class Module(ABC):
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop

    # Methods
    def init(self):
        asyncio.ensure_future(self._make_cli().interact())

    def _make_cli(self, streams=None) -> aioconsole.AsynchronousCli:
        return aioconsole.AsynchronousCli(self.get_commands(), streams=streams)

    def get_commands(self) -> Dict[str, Tuple[Callable, argparse.ArgumentParser]]:
        cmds = {}

        for attr in dir(self):
            obj = getattr(self, attr)

            if is_command(obj):
                cmds[obj.name] = (obj, obj.parser)

        return cmds


# Decorators
def command(name: Optional[str] = None, description: Optional[str] = None):
    parser = argparse.ArgumentParser(description=description)

    def decorator(fun):
        if not is_command(fun):
            fun.__is_command__ = True
            fun.name = name or fun.__name__
            fun.parser = parser

            if not hasattr(fun, 'arguments'):
                fun.arguments = []

            else:
                fun.arguments.reverse()
                for flags, params in fun.arguments:
                    fun.parser.add_argument(*flags, **params)

        return fun

    return decorator


def argument(*flags: str, **others):
    def decorator(fun):
        if 'type' not in others:
            name = others.get('metavar') or others.get('dest') or flags[0].strip('-')
            annot = fun.__annotations__[name]

            if isinstance(annot, type):
                others['type'] = annot

        if not hasattr(fun, 'arguments'):
            fun.arguments = [(flags, others)]

        else:
            fun.arguments.append((flags, others))

        if is_command(fun):
            fun.parser.add_argument(*flags, **others)

        return fun

    return decorator
