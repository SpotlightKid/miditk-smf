#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# setup.py - Setup file for the miditk-smf package
#

from __future__ import print_function

import distutils
import subprocess
import sys

from os.path import dirname, join

from setuptools import setup


def read(*args):
    return open(join(dirname(__file__), *args)).read()


class ToxTestCommand(distutils.cmd.Command):
    """Distutils command to run tests via tox with 'python setup.py test'.

    Please note that in this configuration tox uses the dependencies in
    `requirements/dev.txt`, the list of dependencies in `tests_require` in
    `setup.py` is ignored!

    See https://docs.python.org/3/distutils/apiref.html#creating-a-new-distutils-command
    for more documentation on custom distutils commands.

    """
    description = "Run tests via 'tox'."
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        self.announce("Running tests with 'tox'...", level=distutils.log.INFO)
        return subprocess.call(['tox'])


install_requires = [
    'six',
]

tests_require = [
    # intentionally left empty, test requirements are declared in tox.ini!
]

scripts = [
    join("miditk", "smf", "scripts", "mid2syx.py")
]

if sys.platform.startswith('win') and 'py2exe' in sys.argv:
    try:
        import py2exe  # noqa: F401
    except ImportError:
        print("py2exe not found. Cannot build Windows stand-alone executables "
              "without it. Please install py2exe.", file=sys.stderr)
        sys.exit(1)
    else:
        setup_opts = dict(
            options={'py2exe': {'bundle_files': 1}},
            console=scripts,
            zipfile=None
        )
else:
    setup_opts = dict(
        entry_points={
            'console_scripts': [
                'mid2syx = miditk.smf.scripts.mid2syx:main',
            ]
        },
        cmdclass={
            'test': ToxTestCommand,
        },
        zip_safe=False
    )


# read meta-data from miditk/smf/release.py
exec(read('miditk', 'smf', 'release.py'), {}, setup_opts)


setup(
    long_description=read('README.rst'),
    packages=[
        'miditk',
        'miditk.common',
        'miditk.smf',
        'miditk.smf.scripts'
    ],
    include_package_data=True,
    test_suite='tests',
    install_requires=install_requires,
    tests_require=tests_require,
    **setup_opts
)
