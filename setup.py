from setuptools import find_packages, setup

NAME = "RAS Collection Instrument"
VERSION = "1.0.2"

REQUIRES = []

setup(
    name=NAME,
    version=VERSION,
    description="Collection Instrument API",
    author_email="ras@ons.gov.uk",
    url="",
    keywords=["Collection Instrument API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    long_description="RAS Collection Instrument microservice.",
)
