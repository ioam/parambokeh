#!/usr/bin/env python

import os
import sys

from setuptools import setup

setup_args = dict(
    name='parambokeh',
    description='ParamBokeh provides an easy way to generate a UI for param based classes in the notebook or on bokeh server.',
    version=os.environ.get("VERSIONHACK","0.2.1"),
    url = 'https://ioam.github.io/parambokeh/',
    long_description=open('README.rst').read() if os.path.isfile('README.rst') else 'Consult README.rst',
    author= "pyviz contributors",
    author_email= "dev@pyviz.org",
    license = "BSD 3-Clause",
    platforms=['Windows', 'Mac OS X', 'Linux'],
    packages = ["parambokeh"],
    provides = ["parambokeh"],

    python_requires = ">=2.7",

    install_requires = [
        'param >=1.5.1',
        'bokeh >=0.12.10'
    ],

    tests_require = [
        'holoviews >=1.9.0',
        'pandas',
        'notebook',
        'flake8',
        'pyparsing',
        'pytest',
        'nbsmoke',
    ],

    extras_require = {
        'docs': [
            'nbsite',
            'sphinx_ioam_theme'
        ]
    }

)


if __name__=="__main__":
    setup(**setup_args)
