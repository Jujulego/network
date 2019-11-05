import asyncio

from ssdp.utils import create_ssdp_endpoint

MULTICAST = "239.255.255.250"
PORT = 1900
TTL = 4


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    task = create_ssdp_endpoint(MULTICAST, PORT, ttl=TTL, loop=loop)
    loop.run_until_complete(task)

    loop.run_forever()
