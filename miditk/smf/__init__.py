# -*- coding: utf-8 -*-

from __future__ import absolute_import

import logging

from .converters import (read_varlen, read_bew, sizeof_varlen, tobytestr,  # noqa: F401
                         tointseq, write_bew, write_varlen)  # noqa: F401
from .api import BaseMidiEventHandler, NullMidiEventHandler  # noqa: F401
from .parser import MidiFileParser  # noqa: F401
from .reader import MidiFileReader  # noqa: F401
from .release import version as __version__  # noqa: F401
from .sequence import MidiSequence  # noqa: F401
from .writer import MidiFileWriter  # noqa: F401


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logging.getLogger(__name__).addHandler(NullHandler())
