import asyncio

from typing import Union


def protect_standard_streams(stream: Union[asyncio.StreamReader, asyncio.StreamWriter]):
    if stream.transport is None:
        return

    try:
        fileno = stream.transport.get_extra_info('pipe').fileno()

        if fileno < 3:
            stream.transport._pipe = None

    except (ValueError, OSError):
        return


class StandardStreamReader(asyncio.StreamReader):
    __del__ = protect_standard_streams


class StandardStreamWriter(asyncio.StreamWriter):
    __del__ = protect_standard_streams

    def write(self, data: Union[bytes, str]) -> None:
        if isinstance(data, str):
            data = data.encode()

        super().write(data)


class NonFileStreamReader:
    def __init__(self, stream, *, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self._eof = False
        self._loop = loop
        self._stream = stream

    async def __aiter__(self):
        return self

    async def __anext__(self):
        val = await self.readline()

        if val == b'':
            raise StopAsyncIteration

        return val

    def at_eof(self):
        return self._eof

    async def readline(self):
        data = await self._loop.run_in_executor(None, self._stream.readline)

        if isinstance(data, str):
            data = data.encode()

        self._eof = not data
        return data

    async def read(self, n=-1):
        data = await self._loop.run_in_executor(None, self._stream.read, n)

        if isinstance(data, str):
            data = data.encode()

        self._eof = not data
        return data


class NonFileStreamWriter:
    def __init__(self, stream, *, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self._stream = stream

    def write(self, data: Union[str, bytes]):
        if isinstance(data, bytes):
            data = data.decode()

        self._stream.write(data)

    async def drain(self):
        try:
            flush = self._stream.flush
        except AttributeError:
            pass
        else:
            await self._loop.run_in_executor(None, flush)


StreamReader = Union[StandardStreamReader, NonFileStreamReader]
StreamWriter = Union[StandardStreamWriter, NonFileStreamWriter]
