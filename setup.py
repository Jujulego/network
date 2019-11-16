from setuptools import setup

setup(
    name="network",
    version="0.1",
    packages=["network"],
    install_requires=[
        "asyncio >=3.4.3, <4.0.0",
        "pyee >=6.0.0, <7.0.0"
    ]
)
