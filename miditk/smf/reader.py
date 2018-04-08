# -*- coding: utf-8 -*-
#
# miditk/smf/reader.py
#
"""MidiFileReader combines the MidiFileParser with an event handler."""

from __future__ import absolute_import, unicode_literals

from io import BytesIO

from six import string_types, text_type

# package-specific imports
from .api import NullMidiEventHandler
from .parser import MidiFileParser


__all__ = ('MidiFileReader',)


class MidiFileReader(object):
    """Parse a midi file and trigger the midi events on the outstream object."""

    def __init__(self, infile, handler=None):
        self.infile = infile
        self.handler = handler

    def read(self, strict=True):
        """Start parsing the file."""
        if isinstance(self.infile, string_types):
            self.infile = open(self.infile, 'rb')
            should_close = True
        else:
            should_close = False

        self.parser = MidiFileParser(self.infile, self.handler or NullMidiEventHandler,
                                     strict=strict)
        self.parser.parse_header()
        self.parser.parse_tracks()

        if should_close:
            self.infile.close()

    def set_data(self, data='', encoding='UTF-8'):
        """Set parser data from a plain or byte string."""
        if isinstance(data, text_type):
            data = data.decode(encoding)

        try:
            self.infile.close()
        except (OSError, IOError):
            pass

        self.infile = BytesIO(data)
