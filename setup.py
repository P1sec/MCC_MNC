# -*- coding: UTF−8 -*-

import os
from setuptools import setup


# MCC_MNC Version
VERSION = "0.2.0"


# get long description from the README.md
with open(os.path.join(os.path.dirname(__file__), "README.md")) as fd:
    long_description = fd.read()


setup(
    name="MCC_MNC",
    version=VERSION,
    packages=[
        "mcc_mnc_lut",
        "mcc_mnc_genlib",
        ],
    #
    # cmd-line tools to interrogate the dictionnaries
    scripts=[
        "chk_msisdn.py",
        "chk_mnc.py",
        "chk_cntr.py",
        "chk_ispc.py",
        "conv_pc_383.py",
        ],
    #
    # optional dependencies
    extras_require={
        "dataset_update"  : ["urllib", "csv", "lxml"],
        },
    #
    author="Benoit Michau",
    author_email="benoit.michau@p1sec.com",
    description="A set of lookup tables for identifiers related to mobile operators and accompanying command-line tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/P1sec/MCC_MNC/",
    keywords="MCC MNC MSISDN ISPC country code",
    license="AGPLv3",
    )

