#
# miditk/smf/reader.py
#
"""MidiFileReader combines the MidiFileParser with an event handler."""

from io import BytesIO

# package-specific imports
from .api import NullMidiEventHandler
from .parser import MidiFileParser

__all__ = ("MidiFileReader",)


class MidiFileReader:
    """Parse a midi file and trigger the midi events on the outstream object."""

    def __init__(self, infile, handler=None):
        self.infile = infile
        self.handler = handler

    def read(self, strict=True):
        """Start parsing the file."""
        if isinstance(self.infile, str):
            self.infile = open(self.infile, "rb")
            should_close = True
        else:
            should_close = False

        self.parser = MidiFileParser(
            self.infile, self.handler or NullMidiEventHandler, strict=strict
        )
        self.parser.parse_header()
        self.parser.parse_tracks()

        if should_close:
            self.infile.close()

    def set_data(self, data="", encoding="utf-8"):
        """Set parser data from a plain or byte string."""
        if isinstance(data, str):
            data = data.decode(encoding)

        try:
            self.infile.close()
        except (OSError, IOError):
            pass

        self.infile = BytesIO(data)
