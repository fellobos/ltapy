from setuptools import find_packages, setup

from lighttools import __version__

setup(
    name="ltapy",
    version=__version__,
    description="Python interface for LightTools",
    author="Florian Boesl",
    author_email="f.boesl@osram.com",
    platforms=["any"],  # or more specific, e.g. "win32", "cygwin", "osx"
    license="BSD",
    packages=find_packages(),
)
