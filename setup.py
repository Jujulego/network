from setuptools import setup

REQUIREMENTS = open('requirements.txt').readlines()

setup(
    name="network",
    version="0.1",
    packages=["network"],
    install_requires=REQUIREMENTS
)
