import logging

from .api import BaseMidiEventHandler, MidiEvent, NullMidiEventHandler  # noqa: F401
from .converters import tobytestr  # noqa: F401
from .converters import (  # noqa: F401
    read_bew,
    read_varlen,
    sizeof_varlen,
    tointseq,
    write_bew,
    write_varlen,
)
from .parser import MidiFileParser  # noqa: F401
from .reader import MidiFileReader  # noqa: F401
from .sequence import MidiSequence  # noqa: F401
from .version import version as __version__  # noqa: F401
from .writer import BaseMidiFileWriter, MidiFileWriter  # noqa: F401


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


logging.getLogger(__name__).addHandler(NullHandler())
