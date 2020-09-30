#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File: setup.py
Github: https://github.com/eikemoe/meetingalarm
Description: Meeting Alarm Trayer
"""

import os
import py_compile

try:
    from setuptools import setup, Distribution, find_packages
    from setuptools.command.build_py import build_py
except ImportError:
    from distutils.core import setup, Distribution, find_packages
    from distutils.command.build_py import build_py


# Get the long description from the README file
here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.markdown'), encoding='utf-8') as f:
    description_content = f.read()

separator_content = '## License\n'

with open(os.path.join(here, 'LICENSE'), encoding='utf-8') as f:
    license_content = f.read()

long_description = '\n'.join(
    (description_content, separator_content, license_content)
)

CONFIG = {
    # information
    'classifiers': [
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
    ],
    'description': 'Tray Icon for Meeting Alarm',
    'long_description': long_description,
    'author': [
        'Eike Moehlmann',
    ],
    #'url': '',
    #'download_url': '',
    'author_email': [
        'eike.moehlmann@informatik.uni-oldenburg.de',
    ],
    'name': 'meetingalarm',
    'license': 'custom',
    # deps
    'install_requires': [
        "PyQt5",
        "icalevents",
        "notify2",
        "setuptools",
    ],
    'extras_require': {
    },
    # packages
    'packages': find_packages('src'),
    'package_dir': {
        '':'src'
    },
    'data_files' : [
        ('share/licenses/meetingalarm', [
            'LICENSE',
        ]),
        ('share/doc/meetingalarm', [
            'README.markdown',
        ]),
    ],
    'entry_points': {
        'console_scripts': [
        ],
        'gui_scripts': [
            'meetingalaram = meetingalarm.trayer:main',
        ]
    },
}

setup(
    version="0.2.0",
    **CONFIG
)
