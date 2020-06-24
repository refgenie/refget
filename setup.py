#! /usr/bin/env python

import os
from setuptools import setup
import sys

PACKAGE = "refget"

# Additional keyword arguments for setup().
extra = {}

# Ordinary dependencies
DEPENDENCIES = []
with open("requirements/requirements-all.txt", "r") as reqs_file:
    for line in reqs_file:
        if not line.strip():
            continue
        DEPENDENCIES.append(line)

extra["install_requires"] = DEPENDENCIES

with open("{}/_version.py".format(PACKAGE), 'r') as versionfile:
    version = versionfile.readline().split()[-1].strip("\"'\n")

long_description = open('README.md').read()

setup(
    name=PACKAGE,
    packages=[PACKAGE],
    version=version,
    description="Python client for refget",
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="genome, assembly, bioinformatics, reference, sequence",
    url="https://github.com/databio/refget",
    author=u"Nathan Sheffield, Michal Stolarczyk",
    author_email=u"nathan@code.databio.org", 
    license="BSD2",
    entry_points={
        "console_scripts": [
            'refget = refget.refget:main'
        ],
    },    
    # package_data={"refget": [os.path.join("refget", "*")]},
    include_package_data=True,
    test_suite="tests",
    tests_require=(["mock", "pytest"]),
    setup_requires=(["pytest-runner"] if {"test", "pytest", "ptr"} & set(sys.argv) else []),
    **extra
)
