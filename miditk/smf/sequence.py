# -*- coding: utf-8 -*-
#
# miditk/smf/sequence.py
#
"""A MIDI stream event handler class to convert an SMF file into a container
object for a sequence of MIDI time-stamped events."""

from __future__ import absolute_import, print_function, unicode_literals

# standard library imports
import logging
from itertools import groupby
from operator import attrgetter

# package-specific imports
from ..common.constants import (END_OF_EXCLUSIVE, END_OF_TRACK, KEY_SIGNATURE, SEQUENCE_NAME,
                                SYSTEM_EXCLUSIVE, TEMPO, TIME_SIGNATURE)
from .api import BaseMidiEventHandler
from .converters import tointseq
from .reader import MidiFileReader


__all__ = ('MidiSequence', 'ObjectMidiEventHandler')
log = logging.getLogger(__name__)


class MidiSequence(list):
    """Container for a sequence of time-stamped MIDI events."""

    def __init__(self, *args, **kwargs):
        super(MidiSequence, self).__init__(*args, **kwargs)
        self.tracks = {}

    def __repr__(self):
        title = getattr(self, 'sequence_name', '')
        return "<MidiSequence tracks=%i events=%i, title='%s'>" % (
            self.num_tracks, len(self), title)

    def dump_events(self):
        for i, ev in enumerate(sorted(self, key=attrgetter('time', 'track'))):
            if ev.channel is not None:
                print("%03i: Channel event - type: %02XH, channel: %X, data: %r [%.2f]" %
                      (i, ev.type, ev.channel, tointseq(ev.data), ev.time))
            elif ev.meta_type:
                print('%03i: Meta event - type: %02XH, data: %r [%.2f]' % (
                      i, ev.meta_type, tointseq(ev.data), ev.time))
            elif ev.type == SYSTEM_EXCLUSIVE:
                print('%03i: Sysex_event - size: %i [%.2f]' % (
                      i, len(ev.data) + 1, ev.time))

    def events_by_time(self):
        return groupby(sorted(self, key=attrgetter('time', 'track')),
                       key=attrgetter('time'))

    def events_by_track(self):
        return groupby(sorted(self, key=attrgetter('track', 'time')),
                       key=attrgetter('track'))

    def channel_message_events(self, track=None):
        for event in sorted(self, key=attrgetter('track', 'time')):
            if event.channel and (track is None or event.track == track):
                yield event

    def meta_events(self, track=None):
        for event in sorted(self, key=attrgetter('track', 'time')):
            if event.meta_type and (track is None or event.track == track):
                yield event

    def sysex_events(self, track=None):
        for event in sorted(self, key=attrgetter('time', 'track')):
            if (event.type == SYSTEM_EXCLUSIVE and
                    (track is None or event.track == track)):
                yield event

    @classmethod
    def fromfile(cls, filename, debug=False):
        sequence = cls()
        midiin = MidiFileReader(filename,
                                ObjectMidiEventHandler(sequence, debug=debug))
        midiin.read()
        return sequence


class ObjectMidiEventHandler(BaseMidiEventHandler):
    """Collects all information from a MIDI file in a container object.

    On class instantiation you need to pass an instance to the constructor,
    which supports the Python list interface and attribute assignment. If
    None is passed (the default), a ``MidiSequence`` instance will be created
    and used instead.

    """
    meta_events = ['copyright', 'cuepoint', 'device_name', 'end_of_track',
                   'instrument_name', 'key_signature', 'lyric', 'marker',
                   'midi_ch_prefix', 'midi_port', 'program_name', 'sequence_name',
                   'sequence_number', 'sequencer_specific', 'smtp_offset', 'tempo',
                   'text', 'time_signature']
    channel_events = ['aftertouch', 'channel_pressure', 'controller_change',
                      'note_off', 'note_on', 'pitch_bend', 'program_change']

    def __init__(self, instance=None, debug=False):
        if instance is None:
            instance = MidiSequence()
        BaseMidiEventHandler.__init__(self)
        self._instance = instance
        self.current_time = 0.0
        self.current_tempo = 500000
        self.tick_division = 96
        self.running_status = None
        self._sysex_continuation = False
        self._sysex_buffer = None
        self.debug = debug

    def __getattr__(self, name):
        if name in self.meta_events:
            return self.meta_event
        elif name in self.channel_events:
            return self.channel_message
        else:
            raise AttributeError(name)

    #########################
    ## time handling event handlers.
    ## They should be overwritten with care

    def update_ticks(self, ticks=0, relative=True):
        """Update the global time."""
        BaseMidiEventHandler.update_ticks(self, ticks, relative)
        self.current_time += ticks * (self.current_tempo / 1000.0 /
                                      self._instance.tick_division)
        if self.debug:
            log.debug("Timer update: %s ticks", ticks)

    def add_event(self, event, track=None):
        """Add given event to the container object.

        Takes care of adding the current sequence time to the object.

        """
        event.time = self.current_time
        event.relative_time = self.relative_time
        event.track = self.current_track if track is None else track
        self._instance.append(event)

    #########################
    ## Parsing (non-midi) events

    ## MIDI file header handler

    def header(self, format=0, num_tracks=1, tick_division=96, metrical=True,
               fps=0xE7, frame_resolution=0x28):
        """Handle MIDI file header."""
        for key, value in locals().items():
            if key != 'self' and not key.startswith('_'):
                setattr(self._instance, key, value)
        if metrical:
            log.debug("MIDI file format: %s, no. of tracks: %i, "
                      "tick division: %i ppqn", format, num_tracks, tick_division)
        else:
            log.debug("MIDI file format: %s, no. of tracks: %i, fps: %i, "
                      "resolution: %i", format, num_tracks, fps, frame_resolution)

    def eof(self):
        """Handle end of MIDI file."""
        self.current_track = None

        if self.debug:
            log.debug("End of file reached.")

    def start_of_track(self, track):
        """Handle start of new track."""
        if self.debug:
            log.debug("Start of track #%i.", track)

        self.current_track = track

    #############################
    ## Channel events

    def channel_message_event(self, event, *args):
        """Handle channel messages events."""
        if self.debug:
            log.debug("Channel message event: %s", event)
        self.add_event(event)

    ###############
    ## sysex event

    def invalid_event(self, event):
        """Handle invalid events."""
        log.warning("Received invalid event type (%X) of %i bytes.",
                    event.type, len(event.data))

    def sysex_event(self, event):
        """Handle system exclusive message events.

        ..note:
            Some MIDI files contain sysex messages which are distributed over
            several events, where the event containing the first part of the
            message has the normal 0xF0 status but the following events have
            a 0xF7 (normally used for escape sequence) and no start-of-sysex,
            i.e. all data bytes. The last part of the message in the sequence
            will have end-of-system-exclusive 0xF7 as the last data byte.

            We assemble these sysex messages here into a single sysex event
            with the timestamp of the event with the first part of the message.

        """
        if self.debug:
            log.debug("System exclusive event, %i bytes", len(event.data) + 1)

        if tointseq(event.data)[-1] == END_OF_EXCLUSIVE:
            if self._sysex_continuation:
                if self.debug:
                    log.debug("Sysex continuation in effect. Appending event data.")
                self._sysex_buffer.data += event.data
                event, self._sysex_buffer = self._sysex_buffer, None

            if self.debug:
                log.debug("Storing sysex mssage of %i bytes", len(event.data) + 1)
            self.add_event(event)
            self._sysex_continuation = False
        else:
            if self.debug:
                log.debug("Sysex message not terminated. Assuming continuation.")
            if self._sysex_continuation:
                self._sysex_buffer.data += event.data
            else:
                self._sysex_buffer = event
            self._sysex_continuation = True

    def escape_sequence(self, event):
        if self.debug:
            log.debug("Escape sequence, value: %r" % event.data)
        self.add_event(event)

    #####################
    ## meta events

    def meta_event(self, event, *args):
        """Dispatch meta events."""
        # TEMPO = 0x51 (51 03 tt tt tt (tempo in us/quarternote))
        track = self.current_track

        if event.meta_type == TEMPO:
            b1, b2, b3 = tointseq(event.data)
            event.tempo = (b1 << 16) + (b2 << 8) + b3
            # uses 3 bytes to represent time between quarter
            # notes in microseconds
            self.tempo(event.tempo)

        # TIME_SIGNATURE = 0x58 (58 04 nn dd cc bb)
        elif event.meta_type == TIME_SIGNATURE:
            nn, dd, cc, bb = tointseq(event.data)
            self.time_signature(nn, dd, cc, bb)

        # KEY_SIGNATURE = 0x59 (59 02 sf mi)
        elif event.meta_type == KEY_SIGNATURE:
            sf, mi = tointseq(event.data)
            self.key_signature(sf, mi)

        # SEQUENCE_NAME = 0x03 (03 len text...)
        elif event.meta_type == SEQUENCE_NAME:
            self.sequence_name(event.data)

        # END_OF_TRACK = 0x2F
        elif event.meta_type == END_OF_TRACK:
            self.end_of_track(track)
        else:
            if self.debug:
                log.debug("Meta event: %s", event)

        self.add_event(event, track)

    def end_of_track(self, track=None):
        """Handle end of current track."""
        self.current_track = None

        if self.debug:
            log.debug("End of track #%i.", track)

    def sequence_name(self, name):
        """Handle Sequence / Track name events."""
        name = name.decode('latin1', 'replace')
        if self.current_track == 0:
            if self.debug:
                log.debug("Sequence name: %s", name)
            self._instance.sequence_name = name
        else:
            if self.debug:
                log.debug("Track name (%02i): %s", self.current_track, name)
            self._instance.tracks[self.current_track] = name

    def tempo(self, value):
        """Handle tempo change events."""
        if not hasattr(self._instance, 'initial_tempo'):
            self._instance.initial_tempo = value

        self.current_tempo = value
        if self.debug:
            log.debug("Tempo: %.2f ms/quarter note (%.2f BPM)",
                      value / 1000.0, 60000000.0 / value)

    def time_signature(self, nn, dd, cc, bb):
        """Handle time signature change events."""
        self.current_time_signature = (nn, dd**2)
        if self.debug:
            log.debug("Time signature: %i/%i (%i cpm, %i dpqn)",
                      nn, dd**2, cc, bb)

    def key_signature(self, sf, mi):
        """Handle key signature change events."""
        if self.debug:
            log.debug("Key signature: %s %s", sf, mi)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        test_file = sys.argv[1]
    else:
        print("Usage: sequence.py MIDIFILE")

    logging.basicConfig(level=logging.INFO)
    # do parsing
    sequence = MidiSequence.fromfile(test_file)
    print(sequence)
    sequence.dump_events()
