from setuptools import setup

# Read dependencies
with open('requirements.txt') as f:
    requirements = f.readlines()

# Setup package
setup(
    name="network",
    version="1.1",
    packages=["network",
              "network.base",
              "network.gena",
              "network.soap",
              "network.ssdp",
              "network.utils"],
    install_requires=requirements,
    test_suite='tests',
    tests_require=['pytest']
)
