import asyncio

from pyee import AsyncIOEventEmitter
from typing import Optional


# Class
class EventEmitter(AsyncIOEventEmitter):
    def __init__(self, loop: Optional[AsyncIOEventEmitter] = None):
        if loop is None:
            loop = asyncio.get_event_loop()

        super().__init__(loop)

    # Methods
    async def wait(self, event: str):
        e = asyncio.Event()
        self.on(event, lambda *_: e.set())

        await e.wait()
