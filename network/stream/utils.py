import asyncio
import os
import stat
import sys

from typing import Tuple

from .protocol import StandardStreamReaderProtocol
from .stream import StreamReader, StreamWriter
from .stream import StandardStreamReader, StandardStreamWriter
from .stream import NonFileStreamReader, NonFileStreamWriter


def is_pipe_compatible(pipe) -> bool:
    # Not on windows
    if sys.platform == 'win32':
        return False

    try:
        fileno = pipe.fileno()
        mode = os.fstat(fileno).st_mode
        is_char = stat.S_ISCHR(mode)
        is_fifo = stat.S_ISFIFO(mode)
        is_socket = stat.S_ISSOCK(mode)

        return is_char or is_fifo or is_socket

    except OSError:
        return False


async def open_standard_pipe(
        pipe_in, pipe_out, pipe_err, *, loop=None
) -> Tuple[StandardStreamReader, StandardStreamWriter, StandardStreamWriter]:
    if loop is None:
        loop = asyncio.get_event_loop()

    # Reader
    in_reader = StandardStreamReader(loop=loop)
    protocol = StandardStreamReaderProtocol(in_reader, loop=loop)
    await loop.connect_read_pipe(lambda: protocol, pipe_in)

    # Out writer
    out_transport, _ = await loop.connect_write_pipe(lambda: protocol, pipe_out)
    out_writer = StandardStreamWriter(out_transport, protocol, in_reader, loop)

    # Err writer
    err_transport, _ = await loop.connect_write_pipe(lambda: protocol, pipe_err)
    err_writer = StandardStreamWriter(err_transport, protocol, in_reader, loop)

    return in_reader, out_writer, err_writer


async def create_standard_streams(
        stdin, stdout, stderr, *, loop=None
) -> Tuple[StreamReader, StreamWriter, StreamWriter]:
    if all(map(is_pipe_compatible, (stdin, stdout, stderr))):
        return await open_standard_pipe(stdin, stdout, stderr, loop=loop)

    return (
        NonFileStreamReader(stdin, loop=loop),
        NonFileStreamWriter(stdout, loop=loop),
        NonFileStreamWriter(stderr, loop=loop)
    )


async def get_standard_streams(*, use_stderr=False, loop=None) -> Tuple[StreamReader, StreamWriter]:
    if loop is None:
        loop = asyncio.get_event_loop()

    in_reader, out_writer, err_writer = await create_standard_streams(sys.stdin, sys.stdout, sys.stderr, loop=loop)
    return in_reader, err_writer if use_stderr else out_writer
