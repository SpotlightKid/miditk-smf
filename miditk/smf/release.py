# -*- coding:utf-8 -*-
#
# miditk/smf/release.py - release information for the python-midi package
#

name = 'miditk-smf'
version = '0.2.1'
keywords = 'MIDI, parsing, multimedia, I/O'
author = 'Christopher Arndt'
author_email = 'chris@chrisarndt.de'
url = 'https://github.com/SpotlightKid/miditk-smf'
license = 'MIT License'
description = "A toolkit for working with Standard MIDI files"
platforms = 'POSIX, Windows, MacOS X'
classifiers = """
Development Status :: 4 - Beta
Intended Audience :: Developers
Intended Audience :: End Users/Desktop
License :: OSI Approved :: MIT License
Operating System :: Microsoft :: Windows
Operating System :: POSIX
Operating System :: MacOS :: MacOS X
Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: PyPy
Topic :: Software Development :: Libraries :: Python Modules
Topic :: Multimedia :: Sound/Audio :: MIDI
Topic :: Utilities
"""
classifiers = [c.strip() for c in classifiers.splitlines()
               if c.strip() and not c.startswith('#')]

try:
    del c  # noqa
except NameError:
    pass  # Python 3
