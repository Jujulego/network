import asyncio

from typing import Optional


class StandardStreamReaderProtocol(asyncio.StreamReaderProtocol):
    def connection_made(self, transport: asyncio.transports.BaseTransport) -> None:
        if self._stream_reader._transport is not None:
            return

        super().connection_made(transport)

    def connection_lost(self, exc: Optional[Exception]) -> None:
        if self._stream_reader is not None:
            if exc is None:
                self._stream_reader.feed_eof()
            else:
                self._stream_reader.set_exception(exc)

        if not self._closed.done():
            if exc is None:
                self._closed.set_result(None)
            else:
                self._closed.set_exception(exc)
