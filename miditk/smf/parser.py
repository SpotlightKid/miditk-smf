# -*- coding: utf-8 -*-
#
# miditk/smf/parser.py
#
"""MIDI file low-level binary parsing."""

from __future__ import absolute_import, unicode_literals

# standard library imports
import logging

# package-specific imports
from ..common.constants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, END_OF_EXCLUSIVE,
                                ESCAPE_SEQUENCE, META_EVENT, MONO_PRESSURE, MTC, NOTE_OFF, NOTE_ON,
                                PITCH_BEND, PROGRAM_CHANGE, SONG_POSITION_POINTER, SONG_SELECT,
                                SYSTEM_EXCLUSIVE)
from .converters import read_bew, read_varlen, sizeof_varlen, tointseq


__all__ = ('MidiFileParser', 'ParseError')
log = logging.getLogger(__name__)


# exceptions
class ParseError(Exception):
    pass


# utility functions
def _read_event_data(stream):
    """Read data for next MIDI event from stream.

    Returns a tuple with (size, data).

    """
    data = stream.read(4)
    size = read_varlen(data)
    stream.seek(sizeof_varlen(size) - len(data), 1)
    return size, stream.read(size)


# classes
class MidiEvent(object):
    def __init__(self, type_=META_EVENT, track=0):
        self.type = type_
        self.track = track
        self.meta_type = None
        self.data_size = 0
        self.data = []
        self.channel = None

    def __repr__(self):
        s = "<MidiEvent track=%s" % (self.track,)
        if self.type == SYSTEM_EXCLUSIVE:
            s += " type=sysex len=%i" % (len(self.data),)
        if self.channel is not None:
            s += " ch=%02i status=%X" % (self.channel, self.type)
            s += " data=%r" % (tointseq(self.data),)
        elif self.meta_type:
            s += " type=meta type=%X data=%r" % (self.meta_type, tointseq(self.data))
        return s + '>'

    @property
    def bytes(self):
        """Return event data as a list of single byte int values."""
        return [self.type] + tointseq(self.data)


class MidiFileParser(object):
    """Parser that decodes the raw binary midi data.

    The MidiFileParser is the lowest level parser and generates events from
    the raw midi data, which are processed by the output event handlers.

    The idea is that this class does not retain any status other than is needed
    to parse the raw midi data. Instead it calls methods on the handler object
    whenever an event occurs or the status changes (i.e. parsing events or
    event timings). It is then the responsibility of the handler to keep track
    of status.

    """

    channel_data_sizes = {
        PROGRAM_CHANGE: 1,
        CHANNEL_PRESSURE: 1,
        NOTE_OFF: 2,
        NOTE_ON: 2,
        MONO_PRESSURE: 2,
        CONTROLLER_CHANGE: 2,
        PITCH_BEND: 2,
    }

    system_data_sizes = {
        MTC: 1,
        SONG_POSITION_POINTER: 2,
        SONG_SELECT: 1
    }

    def __init__(self, instream, handler=None, strict=True):
        """Initialize object.

        instream must be an open, readable file-like object for a standard MIDI file.

        The file-like object must support the ``read``, ``seek`` and ``tell` methods.

        """
        self.instream = instream
        self._handler = handler
        self.strict = strict
        self._current_track = None
        self._running_status = None
        self._sysex_continuation = False

    def dispatch(self, methodname, *args, **kwargs):
        try:
            try:
                method = getattr(self._handler, methodname)
            except AttributeError as exc:
                msg = "Method '%s' not implemented by handler." % methodname
                if self.strict:
                    raise AttributeError(msg)
                else:
                    log.warning(msg)
            else:
                method(*args, **kwargs)
        except Exception as exc:
            msg = "Error calling handler '%s'" % methodname

            if args and isinstance(args[0], MidiEvent):
                msg += " for event %r" % args[0]
            else:
                msg += "Args: %r, Kw args: %r " % (args, kwargs)

            if self.strict:
                log.exception(msg)
                raise
            else:
                log.error(msg + str(exc))

    def next_chunk(self):
        chunk_id = self.instream.read(4)

        if not chunk_id:
            raise EOFError("End of file reached.")

        chunk_len = read_bew(self.instream.read(4))
        return chunk_id, chunk_len

    def parse_header(self):
        """Parse the header chunk."""

        chunk_id, chunk_len = self.next_chunk()
        instream = self.instream

        # check if it is a proper midi file
        if chunk_id != b'MThd':
            raise ParseError("Invalid MIDI file header. Chunk identifier must be 'MThd'.")

        # Header values are at fixed locations, so no reason to be clever
        self.format = read_bew(instream.read(2))
        self.num_tracks = read_bew(instream.read(2))

        if self.format == 0 and self.num_tracks > 1:
            msg = ("Invalid number of tracks (%i). Type 0 midi files may only "
                   "contain a single track." % self.num_tracks)

            if self.strict:
                raise ParseError(msg)
            else:
                log.warning(msg)

        tick_div = instream.read(2)
        fps, resolution = tointseq(tick_div)

        if fps & 0x80:
            metrical = False
        else:
            metrical = True
            division = read_bew(tick_div)

        # Theoretically a header larger than 6 bytes can exist
        # but no one has seen one in the wild.
        # We will correctly ignore unknown data if present, though.
        if chunk_len > 6:
            log.warning("Invalid header size (%i). Skipping trailing header "
                        "bytes", chunk_len)
            instream.seek(chunk_len - 6, 1)

        # call the header event handler on the stream
        if metrical:
            self.dispatch('header', self.format, self.num_tracks, metrical=True,
                          tick_division=division)
        else:
            self.dispatch('header', self.format, self.num_tracks, metrical=False,
                          fps=fps, frame_resolution=resolution)

    def parse_track(self, chunk_id, chunk_len):
        """Parse a track chunk.

        This is the most important part of the parser.

        """
        self._running_status = None
        self._sysex_continuation = False

        instream = self.instream
        dispatch = self.dispatch

        # check for proper chunk type
        if chunk_id != b'MTrk':
            raise ParseError("Invalid track chunk identifier '%s', must be 'MTrk'.", chunk_id)

        if self._current_track is None:
            self._current_track = 0
        else:
            self._current_track += 1

        if self._current_track >= self.num_tracks:
            msg = ("Supernumerous track no. %i found. Header says there should "
                   "be only %i tracks." % (self._current_track + 1, self.num_tracks))

            if self.strict:
                raise ParseError(msg)
            else:
                log.warning(msg)

        # Trigger event at the start of a track
        # set time to 0 at start of a track
        dispatch('reset_ticks')
        dispatch('start_of_track', self._current_track)
        # absolute position!
        track_endposition = instream.tell() + chunk_len

        while instream.tell() < track_endposition:
            # find relative time of the event
            ticks = read_varlen(instream.read(4))
            instream.seek(sizeof_varlen(ticks) - 4, 1)

            if ticks > 0:
                dispatch('update_ticks', ticks)

            # be aware of running status!
            status = ord(instream.read(1))

            if status & 0x80:
                # the status byte has the high bit set, so it
                # was not running data but proper status byte
                status = self._running_status = status
            else:
                # use saved running status
                if self._running_status:
                    status = self._running_status
                    instream.seek(-1, 1)
                else:
                    msg = ("Non-status byte 0x%02X encountered at offset %i "
                           "while expecting a status byte and no running status "
                           "in effect.")
                    offset = instream.tell()

                    if self.strict:
                        log.error(msg, status, offset)
                        raise ParseError(msg % (status, offset))
                    else:
                        log.warning(msg, status, offset)
                        log.warning("Trying to re-synchronize.")
                        continue

            # Create event container
            event = MidiEvent(track=self._current_track)

            # Is it a meta event?
            # these only exists in midi files, not in transmitted midi data.
            # In transmitted data META_EVENT (0xFF) is a system reset.
            if status == META_EVENT:
                self._running_status = None
                event.meta_type = ord(instream.read(1))
                event.size, event.data = _read_event_data(instream)
                dispatch('meta_event', event)

            # Is it a sysex event?
            elif status == SYSTEM_EXCLUSIVE:
                self._running_status = None
                event.size, event.data = _read_event_data(instream)
                event.type = SYSTEM_EXCLUSIVE

                # We check for proper terminiation of the sysex msg
                # with an EOX byte, since some manufacturers split up sysex
                # msgs over several events (continuation event).
                if event.data[-1] != END_OF_EXCLUSIVE:
                    self._sysex_continuation = True
                else:
                    self._sysex_continuation = False

                dispatch('sysex_event', event)

            # Escape sequence or sysex continuation message
            elif status == END_OF_EXCLUSIVE:
                self._running_status = None

                event.size, event.data = _read_event_data(instream)
                if self._sysex_continuation:
                    event.type = SYSTEM_EXCLUSIVE

                    if event.data[-1] == END_OF_EXCLUSIVE:
                        self._sysex_continuation = False

                    dispatch('sysex_event', event)
                else:
                    event.type = ESCAPE_SEQUENCE
                    dispatch('escape_sequence', event)

            elif 0xF1 <= status <= 0xFE:
                # Invalid system common or system real time message
                self._running_status = None
                event.data_size = self.system_data_sizes.get(status, 0)
                event.data = instream.read(event.data_size)
                event.type = status
                dispatch('invalid_event', event)

            # Otherwise it must be a channel voice message
            else:
                event.data_size = self.channel_data_sizes.get(status & 0xF0, 0)
                event.data = instream.read(event.data_size)
                event.type = status & 0xF0
                event.channel = status & 0xF
                dispatch('channel_message_event', event)

    def parse_tracks(self):
        """Parse all track chunks."""
        while True:
            try:
                chunk_id, chunk_len = self.next_chunk()
            except EOFError:
                break
            else:
                if chunk_id == b'MTrk':
                    self.parse_track(chunk_id, chunk_len)
                else:
                    self.instream.seek(chunk_len, 1)

        self.dispatch('eof')


if __name__ == '__main__':
    from miditk.smf.api import PrintingMidiEventHandler

    # get data
    test_files = (
        'tests/testdata/minimal.mid',
        'tests/testdata/minimal-cubase-type0.mid',
        'tests/testdata/minimal-cubase-type1.mid',
    )

    # do parsing
    for test_file in test_files:
        with open(test_file, 'rb') as midi_file:
            midi_in = MidiFileParser(midi_file, PrintingMidiEventHandler())
            midi_in.parse_header()
            midi_in.parse_tracks()
            print('')
