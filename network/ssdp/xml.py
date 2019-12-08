import aiohttp
import asyncio
import inspect
import logging

from functools import wraps
from network.utils.asyncio import with_event_loop
from typing import Callable
from xml.etree import ElementTree as ET

from .constants import XML_DEVICE_NS

# Logging
logger = logging.getLogger('ssdp:xml')


# Utils
@with_event_loop
async def get_xml(url: str, *, loop: asyncio.AbstractEventLoop) -> ET.Element:
    logger.debug(f'Getting {url}')

    async with aiohttp.ClientSession(loop=loop) as session:
        async with session.get(url) as response:
            assert response.status == 200, f'Unable to get {url} (status {response.status})'

            data = await response.read()
            return ET.fromstring(data)


def get_device_uuid(xml: ET.Element, url: str) -> str:
    udn = xml.find('upnp:UDN', XML_DEVICE_NS)
    assert udn is not None, f'Invalid description: no UDN element ({url})'

    return udn.text.strip()[5:]


@with_event_loop
async def get_device_xml(url: str, *, loop: asyncio.AbstractEventLoop) -> (ET.Element, str):
    xml = await get_xml(url, loop=loop)

    device = xml.find('upnp:device', XML_DEVICE_NS)
    assert device is not None, f'Invalid description: no device element ({url})'

    return device, get_device_uuid(xml, url)


# Decorator
def log_xml_errors(fun: Callable) -> Callable:
    if inspect.iscoroutinefunction(fun):
        @wraps(fun)
        async def deco(*args, **kwargs):
            try:
                return await fun(*args, **kwargs)

            except aiohttp.ClientError as err:
                logger.error(f'Error while getting description: {err}')

            except AssertionError as err:
                logger.error(str(err))

    else:
        @wraps(fun)
        def deco(*args, **kwargs):
            try:
                return fun(*args, **kwargs)

            except aiohttp.ClientError as err:
                logger.error(f'Error while getting description: {err}')

            except AssertionError as err:
                logger.error(str(err))

    return deco
