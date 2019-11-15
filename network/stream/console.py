import asyncio

from pyee import AsyncIOEventEmitter
from typing import Optional

from .stream import StreamReader, StreamWriter
from .utils import get_standard_streams


class Console(AsyncIOEventEmitter):
    def __init__(self, *, loop: Optional[asyncio.AbstractEventLoop] = None):
        super().__init__(loop or asyncio.get_event_loop())

        # - internals
        self.__started = False
        self.__task = None  # type: Optional[asyncio.Future]
        self._stream_reader = None  # type: Optional[StreamReader]
        self._stream_writer = None  # type: Optional[StreamWriter]

    # Methods
    async def start(self):
        if not self.__started:
            self._stream_reader, self._stream_writer = await get_standard_streams(loop=self._loop)

            self.__started = True
            self.__task = await self._run()

    async def _run(self):
        try:
            while self.__started:
                line = await self._prompt()
                self.emit('input', line)

        finally:
            self.__started = False

    def stop(self):
        if self.__started:
            self.__started = False

    async def _prompt(self) -> str:
        # Write prompt
        self._stream_writer.write(">>> ")
        await self._stream_writer.drain()

        # Read input
        data = await self._stream_reader.readline()
        data = data.decode()

        if not data.endswith('\n'):
            raise EOFError

        return data.rstrip('\n')
