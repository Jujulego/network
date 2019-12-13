import asyncio

from pyee import AsyncIOEventEmitter


# Class
class EventEmitter(AsyncIOEventEmitter):
    # Methods
    async def wait(self, event: str):
        e = asyncio.Event()
        self.on(event, lambda *_: e.set())

        await e.wait()
