# -*- coding: utf-8 -*-
#
# miditk/smf/writer.py
#
"""Event handler, which writes back MIDI events to a Standard MIDI File."""

from __future__ import absolute_import, unicode_literals

from io import BytesIO

from six import text_type

from ..common.constants import (ACTIVE_SENSING, CHANNEL_PRESSURE, CONTROLLER_CHANGE, COPYRIGHT,
                                CUEPOINT, END_OF_EXCLUSIVE, END_OF_TRACK, ESCAPE_SEQUENCE, FPS_25,
                                INSTRUMENT_NAME, KEY_SIGNATURE, LYRIC, MARKER, META_EVENT,
                                MIDI_CH_PREFIX, MIDI_TIME_CODE, MONO_PRESSURE, NOTE_OFF, NOTE_ON,
                                PITCH_BEND, PROGRAM_CHANGE, SEQUENCE_NAME, SEQUENCE_NUMBER,
                                SEQUENCER_SPECIFIC, SMTP_OFFSET, SONG_CONTINUE,
                                SONG_POSITION_POINTER, SONG_SELECT, SONG_START, SONG_STOP,
                                SYSTEM_EXCLUSIVE, TEMPO, TEXT, TIME_SIGNATURE, TIMING_CLOCK,
                                TRACK_HEADER, TUNING_REQUEST)
from .api import NullMidiEventHandler
from .converters import tobytestr, write_bew, write_varlen

__all__ = ('MidiFileWriter',)


class MidiFileWriter(NullMidiEventHandler):
    """MidiOutFile writes out MIDI events to a Standard MIDi FIle.

    It subclasses :class:`.NullMidiEventHandler`. For the documentation of method params, see the
    corresponding methods there and in its base class :class:`.BaseMidiEventHandler`.

    """

    def __init__(self, fp, encoding='UTF-8'):
        self._file = fp
        self._track_buffer = None
        super(MidiFileWriter, self).__init__(encoding='UTF-8')

    def event_slice(self, slc):
        """Write the event to the current track.

        Correctly inserts a varlen event timestamp too.

        """
        self._write_varlen(self.relative_time)
        self._write(slc)
        self.update_ticks()

    def _write(self, data):
        """Write the next text slice to the raw data."""
        if isinstance(data, text_type):
            data = data.encode()

        if self._track_buffer is not None:
            self._track_buffer.write(data)
        else:
            self._file.write(data)

    def _write_bew(self, value, length=1):
        """Write a value to the file as big endian word."""
        self._write(write_bew(value, length))

    def _write_varlen(self, value):
        """Write a variable length word to the file."""
        self._write(write_varlen(value))

    #####################
    ## File (non-midi) events

    def header(self, format=0, num_tracks=1, tick_division=96, metrical=True,
               fps=FPS_25, frame_resolution=40):
        """Add MIDI file header chunk.

        For params see :meth:`.BaseMidiEventHandler.header`.

        """
        self._write('MThd')
        self._write_bew(6, 4)  # header size
        self._write_bew(format, 2)
        self._write_bew(num_tracks, 2)

        if metrical:
            # timing devision is in pulses per quarter note (ppqn)
            self._write_bew(tick_division & 32767, 2)
        else:
            # timing devision is in frames per second (fps), frame resolution
            self._write_bew(fps, 1)
            self._write_bew(frame_resolution, 1)

    def start_of_track(self, track=None):
        """Handle start of track meta event.

        :param int track: number of track (None = current track + 1)

        """
        if track is None:
            if self.current_track is None:
                track = 0
            else:
                track = self.current_track + 1

        self.current_track = track
        self._track_buffer = BytesIO()

    #####################
    ## Midi events

    def channel_pressure(self, channel, pressure):
        """Handle channel (mono) pressure event."""
        self.event_slice(tobytestr([CHANNEL_PRESSURE + channel, pressure]))

    def controller_change(self, channel, controller, value):
        """Handle controller change event."""
        self.event_slice(tobytestr([CONTROLLER_CHANGE + channel, controller, value]))

    def note_off(self, channel=0, note=0x40, velocity=0x40):
        """Handle note off event."""
        self.event_slice(tobytestr([NOTE_OFF + channel, note, velocity]))

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        """Handle note on event."""
        self.event_slice(tobytestr([NOTE_ON + channel, note, velocity]))

    def pitch_bend(self, channel, value):
        """Handle pitch bend event."""
        msb = (value >> 7) & 0xFF
        lsb = value & 0xFF
        self.event_slice(tobytestr([PITCH_BEND + channel, msb, lsb]))

    def poly_pressure(self, channel=0, note=0x40, pressure=0x40):
        """Handle poly pressure (aftertouch) event."""
        self.event_slice(tobytestr([MONO_PRESSURE + channel, note, pressure]))

    def program_change(self, channel, program):
        """Handle program change event."""
        self.event_slice(tobytestr([PROGRAM_CHANGE + channel, program]))

    #####################
    ## System Exclusive

    def system_exclusive(self, data):
        """Handle system exclusive (sysex) message."""
        sysex_len = write_varlen(len(data) + 1)
        self.event_slice(tobytestr(SYSTEM_EXCLUSIVE) + sysex_len + data +
                         tobytestr(END_OF_EXCLUSIVE))

    #####################
    ## Meta events

    def meta_slice(self, meta_type, data):
        """Write a meta event."""
        if isinstance(data, text_type):
            data = data.encode(self.encoding, errors='surrogateescape')

        self.event_slice(tobytestr([META_EVENT, meta_type]) +
                         write_varlen(len(data)) + data)

    def end_of_track(self, track=None):
        """Handle end of track meta event.

        Writes the track to the buffer.

        """
        track_data = self._track_buffer.getvalue()
        self._track_buffer = None
        # we need to know size of track data.
        eot_slice = write_varlen(self.relative_time) + tobytestr(
            [META_EVENT, END_OF_TRACK, 0])
        self._write(TRACK_HEADER)
        self._write_bew(len(track_data) + len(eot_slice), 4)
        # then write
        self._write(track_data)
        self._write(eot_slice)

    def copyright(self, text):
        """Handle copyright notice meta event."""
        self.meta_slice(COPYRIGHT, text)

    def cuepoint(self, text):
        """Handle cuepoint meta event."""
        self.meta_slice(CUEPOINT, text)

    def instrument_name(self, text):
        """Handle instrument name meta event."""
        self.meta_slice(INSTRUMENT_NAME, text)

    def key_signature(self, sf, mi):
        """Handle key signature meta event."""
        self.meta_slice(KEY_SIGNATURE, tobytestr([sf, mi]))

    def lyric(self, text):
        """Handle lyrics meta event."""
        self.meta_slice(LYRIC, text)

    def marker(self, text):
        """Handle marker meta event."""
        self.meta_slice(MARKER, text)

    def midi_ch_prefix(self, channel):
        """Handle MIDI channel prefix meta event."""
        self.meta_slice(MIDI_CH_PREFIX, tobytestr([channel]))

    def midi_port(self, value):
        """Handle MIDI port meta event."""
        self.meta_slice(MIDI_CH_PREFIX, tobytestr([value]))

    def sequence_name(self, text):
        """Handle sequence/track name meta event."""
        self.meta_slice(SEQUENCE_NAME, text)

    def sequence_number(self, value):
        """Handle sequence number meta event."""
        self.meta_slice(SEQUENCE_NUMBER, write_bew(value, 2))

    def sequencer_specific(self, data):
        """Handle sequencer specific meta event."""
        self.meta_slice(SEQUENCER_SPECIFIC, data)

    def smtp_offset(self, hour, minute, second, frame, frame_part):
        """Handle SMTP offset meta event."""
        self.meta_slice(SMTP_OFFSET,
                        tobytestr([hour, minute, second, frame, frame_part]))

    def tempo(self, value):
        """Handle tempo meta event."""
        hb, mb, lb = (value >> 16 & 0xff), (value >> 8 & 0xff), (value & 0xff)
        self.meta_slice(TEMPO, tobytestr([hb, mb, lb]))

    def text(self, text):
        """Handle text meta event."""
        self.meta_slice(TEXT, text)

    def time_signature(self, nn, dd, cc, bb):
        """Handle time signature meta event."""
        self.meta_slice(TIME_SIGNATURE, tobytestr([nn, dd, cc, bb]))

    def unknown_meta_event(self, meta_type, data):
        """Handle any undefined meta events."""
        self.meta_slice(meta_type, tobytestr(data))

    #####################
    ## Common events
    ##
    ## These should only occur in real-time MIDI data, not in Standard MIDI Files.

    def midi_time_code(self, msg_type, values):
        """Handle MIDI time code (MTC) quarter frame system common event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        :param int msg_type: 0-7
        :param int values: 0-15

        """
        value = (msg_type << 4) + values
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 2, MIDI_TIME_CODE, value]))

    def song_position_pointer(self, value):
        """Handle song position pointer (SPP) system common event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        :param int value: 0-16383

        """
        lsb = (value & 0x7F)
        msb = (value >> 7) & 0x7F
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 3, SONG_POSITION_POINTER, lsb, msb]))

    def song_select(self, song_number):
        """Handle song select system common event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        :param int song_number: 0-127

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 2, SONG_SELECT, song_number]))

    def tuning_request(self):
        """Handle tuning request system common event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        Takes no arguments.

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 1, TUNING_REQUEST]))

    #####################
    ## Real-time events
    ##
    ## These should only occur in real-time MIDI data, not in Standard MIDI Files.

    def timing_clock(self):
        """Handle MIDI timing clock system real-time event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        Takes no arguments.

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 1, TIMING_CLOCK]))

    def song_start(self):
        """Handle song start system real-time event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        Takes no arguments.

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 1, SONG_START]))

    def song_stop(self):
        """Handle song stop system real-time event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        Takes no arguments.

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 1, SONG_STOP]))

    def song_continue(self):
        """Handle song continue system real-time event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        Takes no arguments.

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 1, SONG_CONTINUE]))

    def active_sensing(self):
        """Handle active sensing system real-time event.

        This should only occur in real-time MIDI data, in Standard MIDI Files it must be embedded
        in an escape sequence meta event.

        Takes no arguments.

        """
        self.event_slice(tobytestr([ESCAPE_SEQUENCE, 1, ACTIVE_SENSING]))

    def system_reset(self):
        """Handle system reset system real-time event.

        This can only occur in real-time MIDI data, in Standard MIDI Files 0xFF marks a meta event,
        so it is ignored.

        Takes no arguments.

        """
        pass
