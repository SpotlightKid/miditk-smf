# -*- coding: utf-8 -*-
#
# miditk/smf/api.py
#
"""MIDI file parsing event handler classes"""

from __future__ import absolute_import, print_function, unicode_literals

# package-specific imports
from ..common.constants import (CHANNEL_PRESSURE, CONTROLLER_CHANGE, COPYRIGHT, CUEPOINT,
                                DEVICE_NAME, END_OF_TRACK, INSTRUMENT_NAME, KEY_SIGNATURE, LYRIC,
                                MARKER, MIDI_CH_PREFIX, MIDI_PORT, NOTE_OFF, NOTE_ON, PITCH_BEND,
                                POLYPHONIC_PRESSURE, PROGRAM_CHANGE, PROGRAM_NAME, SEQUENCE_NAME,
                                SEQUENCE_NUMBER, SEQUENCER_SPECIFIC, SMTP_OFFSET, TEMPO, TEXT,
                                TIME_SIGNATURE)
from .converters import read_bew, tointseq


__all__ = (
    'BaseMidiEventHandler',
    'NullMidiEventHandler',
    'PrintingMidiEventHandler'
)


class BaseMidiEventHandler(object):
    """Dispatch events to specific event handler methods.

    Analyses MIDI events (i.e. channel message and meta events) and calls
    appropriate methods according to the type of the event on the handler
    instance.

    Also keeps track of event times and maintains a running absolute time
    and a relative time between events. Time values are in absolute
    tick values from the opening of a stream.

    This class must be subclassed by a concrete event handler class, which
    implements all the methods to handle specific types of events.

    Sysex and invalid events are silently ignored by default, overwrite the
    ``sysex_event`` and ``invalid_event`` methods in a subclass to handle them.

    """

    def __init__(self, encoding='UTF-8'):
        """Initialize event dispatcher with given output event handler."""
        self.encoding = encoding
        self.absolute_time = 0
        self.relative_time = 0
        self.current_track = None

        # public flags

        # A note_on with a velocity of 0x00 is actually the same as a
        # note_off with a velocity of 0x40. When
        # "convert_zero_velocity" is set, the zero velocity note_on's
        # automatically gets converted into note_off's. This is a less
        # suprising behaviour for those that are not into the intimate
        # details of the midi spec.
        self.convert_zero_velocity = True
        self.dispatch_controllers = False

    ## Handle parsing events, i.e. non-midi, file structure and timing events

    #############################
    ## MIDI file header handler

    def header(self, format, num_tracks, tick_division=96, metrical=True,
               fps=0xE7, frame_resolution=0x28):
        """Handle file header event.

        :param int format: type of midi file in [0, 1, 2]
        :param int num_tracks: number of tracks. Must be 1 track for type 0 file
        :param int tick_division: timing division, i.e. 96 ppqn.
        :param bool metrical: whether to use metrical timing (tick_division) or timecode
            (fps / frame_resolution)
        :param int fps: frames per second as negative 2-complement
        :param int frame_resolution: number of subframes per frame

        """
        pass

    #############################
    ## Parsing (non-midi) events

    def eof(self):
        """Handle end of file event.

        Does nothing by default and can be safely overwritten in a subclass.

        """
        self.current_track = None

    def start_of_track(self, track):
        """Handle start of track event.

        Saves the track number in the instance attribute ``current_track``
        for use by the other event handler methods.

        """
        self.current_track = track

    def reset_ticks(self):
        """Reset time to zero.

        If you overwite this in a sub class, be sure to call this method from
        the base class.

        """
        self.relative_time = 0
        self.absolute_time = 0

    def update_ticks(self, ticks=0, relative=True):
        """Update the global time.

        If ``relative`` is True, ``ticks`` is relative, else it's absolute.

        If you overwite this in a sub class, be sure to call this method from
        the base class.

        """
        if relative:
            self.relative_time = ticks
            self.absolute_time += ticks
        else:
            self.relative_time = ticks - self.absolute_time
            self.absolute_time = ticks

    #############################
    ## Track events

    ## Ignored events

    def invalid_event(self, event):
        """Handle invalid system common or system real time messages.

        Does nothing by default and can be safely overwritten in a subclass.

        :param event: :class:`.MidiEvent` with 0xF1 <= event.type <= 0xFE

        """
        pass

    def escape_sequence(self, event):
        """Handle escape sequence.

        Does nothing by default and can be safely overwritten in a subclass.

        :param event: :class:`.MidiEvent` of type ``ESCAPE_SEQUENCE``

        """
        pass

    # Dispatchers for sysex, channel and meta events

    def sysex_event(self, event):
        """Handle sysex events.

        Calls ``system_exclusive`` method on the handler and passes the message data as a byte
        string.

        :param event: :class:`.MidiEvent` of type ``SYSTEM_EXCLUSIVE``

        """
        self.sysex_message(event.data)

    def channel_message_event(self, event):
        """Dispatch channel message events.

        Examines the message type, parses the event data according to type and
        calls an appropriate event handler method with the event data.

        Type and number of arguments of the handler methods vary depending on
        the event type.

        :param event: :class:`.MidiEvent` with 0x80 <= event.type <= 0xE0

        """
        data = tointseq(event.data)

        if event.type == NOTE_ON:
            note, velocity = data
            # note_on with velocity 0x00 are same as note
            # off with velocity 0x40 according to spec!
            if velocity == 0 and self.convert_zero_velocity:
                self.note_off(event.channel, note, 0x40)
            else:
                self.note_on(event.channel, note, velocity)

        elif event.type == NOTE_OFF:
            note, pressure = data
            self.note_off(event.channel, note, pressure)

        elif event.type == POLYPHONIC_PRESSURE:
            note, pressure = data
            self.poly_pressure(event.channel, note, pressure)

        elif event.type == CONTROLLER_CHANGE:
            controller, value = data
            self.controller_change(event.channel, controller, value)

        elif event.type == PROGRAM_CHANGE:
            program = data[0]
            self.program_change(event.channel, program)

        elif event.type == CHANNEL_PRESSURE:
            pressure = data[0]
            self.channel_pressure(event.channel, pressure)

        elif event.type == PITCH_BEND:
            hibyte, lobyte = data
            value = (hibyte << 7) + lobyte
            self.pitch_bend(event.channel, value)

        else:
            self.unknown_channel_message(event.type, data)

    def meta_event(self, event):
        """Dispatch meta events.

        Examines the message type, parses the event data according to type and
        calls an appropriate event handler method with the event data.

        Type and number of arguments of the handler methods vary depending on
        the event type.

        :param event: :class:`.MidiEvent` of type <= ``META_EVENT``

        """
        data = event.data

        # Events sorted by most common first for optimization

        # END_OF_TRACK = 0x2F (2F 00)
        if event.meta_type == END_OF_TRACK:
            self.end_of_track(self.current_track)
            self.current_track = None

        # TEMPO = 0x51 (51 03 tt tt tt (tempo in us/quarternote))
        elif event.meta_type == TEMPO:
            b1, b2, b3 = tointseq(data)
            # uses 3 bytes to represent time between quarter
            # notes in microseconds
            self.tempo((b1 << 16) + (b2 << 8) + b3)

        # TIME_SIGNATURE = 0x58 (58 04 nn dd cc bb)
        elif event.meta_type == TIME_SIGNATURE:
            nn, dd, cc, bb = tointseq(data)
            self.time_signature(nn, dd, cc, bb)

        # KEY_SIGNATURE = 0x59 (59 02 sf mi)
        elif event.meta_type == KEY_SIGNATURE:
            sf, mi = tointseq(data)
            self.key_signature(sf, mi)

        # SEQUENCE_NAME = 0x03 (03 len text...)
        elif event.meta_type == SEQUENCE_NAME:
            self.sequence_name(data)

        # PROGRAM_NAME = 0x08 (05 len text...)
        elif event.meta_type == PROGRAM_NAME:
            self.program_name(data)

        # INSTRUMENT_NAME = 0x04 (04 len text...)
        elif event.meta_type == INSTRUMENT_NAME:
            self.instrument_name(data)

        # TEXT = 0x01 (01 len text...)
        elif event.meta_type == TEXT:
            self.text(data)

        # COPYRIGHT = 0x02 (02 len text...)
        elif event.meta_type == COPYRIGHT:
            self.copyright(data)

        # SEQUENCE_NUMBER = 0x00 (00 02 ss ss (seq-number))
        elif event.meta_type == SEQUENCE_NUMBER:
            number = read_bew(data)
            self.sequence_number(number)

        # LYRIC = 0x05 (05 len text...)
        elif event.meta_type == LYRIC:
            self.lyric(data)

        # MARKER = 0x06 (06 len text...)
        elif event.meta_type == MARKER:
            self.marker(data)

        # CUEPOINT = 0x07 (07 len text...)
        elif event.meta_type == CUEPOINT:
            self.cuepoint(data)

        # DEVICE_NAME = 0x09 (09 len text...)
        elif event.meta_type == DEVICE_NAME:
            self.device_name(data)

        # MIDI_CH_PREFIX = 0x20 (20 01 channel)
        elif event.meta_type == MIDI_CH_PREFIX:
            channel = read_bew(data)
            self.midi_ch_prefix(channel)

        # MIDI_PORT  = 0x21 (21 01 port (legacy stuff))
        elif event.meta_type == MIDI_PORT:
            port = read_bew(data)
            self.midi_port(port)

        # SMTP_OFFSET = 0x54 (54 05 hh mm ss ff xx)
        elif event.meta_type == SMTP_OFFSET:
            hour, minute, second, frame, framePart = tointseq(data)
            self.smtp_offset(hour, minute, second, frame, framePart)

        # SEQUENCER_SPECIFIC = 0x7F (Sequencer specific event)
        elif event.meta_type == SEQUENCER_SPECIFIC:
            meta_data = tointseq(data)
            self.sequencer_specific(meta_data)

        # Handles any undefined meta events
        else:  # undefined meta type
            meta_data = tointseq(data)
            self.unknown_meta_event(event.meta_type, meta_data)


class NullMidiEventHandler(BaseMidiEventHandler):
    """NullMidiEventHandler handles all MIDI events by doing nothing.

    It can serve as a base class for your specific MIDI event handler classes
    where you only want to handle some events and ignore all others.

    """

    #####################
    ## Channel mesages

    def channel_pressure(self, channel, pressure):
        """Handle channel (mono) change message.

        :param int channel: 0-15
        :param int pressure: 0-127

        """
        pass

    def controller_change(self, channel, controller, value):
        """Handle controller change message.

        :param int channel: 0-15
        :param int controller: 0-127
        :param int value: 0-127

        """
        pass

    def note_off(self, channel=0, note=0x40, velocity=0x40):
        """Handle Note off message.

        :param int channel: 0-15
        :param int note: 0-127
        :param int velocity: 0-127

        """
        pass

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        """Handle Note on message.

        :param int channel: 0-15
        :param int note: 0-127
        :param int velocity: 0-127

        """
        pass

    def poly_pressure(self, channel=0, note=0x40, velocity=0x40):
        """Handle poly pressure message.

        :param int channel: 0-15
        :param int note: 0-127
        :param int velocity: 0-127

        """
        pass

    def pitch_bend(self, channel, value):
        """Handle pitch bend message.

        :param int channel: 0-15
        :param int value: 0-16383

        """
        pass

    def program_change(self, channel, program):
        """Handle program change message.

        :param int channel: 0-15
        :param int program: 0-127

        """
        pass

    def unknown_channel_message(self, status, data):
        """Handle unrecognized channel messages."""
        pass

    #####################
    ## System exclusive events

    def system_exclusive(self, data):
        """Handle system exclusive messsage.

        :param bytes data: byte string of values in range(128)

        """
        pass

    #####################
    ## Meta events

    def copyright(self, text):
        """Handle copyright notice event.

        :param str text: copyright text

        """
        pass

    def cuepoint(self, text):
        """Handle cue point event.

        :param str text: cue point text

        """
        pass

    def device_name(self, text):
        """Handle device name event.

        :param str text: device name

        """
        pass

    def end_of_track(self, track=None):
        """Handle end of track event.

        :param int track: number of track (None = current track)

        """
        pass

    def instrument_name(self, text):
        """Handle instrument name event.

        :param str text: instrument name

        """
        pass

    def key_signature(self, sf, mi):
        """Handle key signature event.

        :param int sf: a byte specifying the number of flats (-ve) or sharps (+ve) which
          identifies the key signature (-7 = 7 flats, -1 = 1 flat, 0 = key of C, 1 = 1 sharp, etc).
        :param int mi: a byte specifying a major (0) or minor (1) key.

        """
        pass

    def lyric(self, text):
        """Handle lyric event.

        :param str text: lyric text

        """
        pass

    def marker(self, text):
        """Handle text marker event.

        :param str text: marker text

        """
        pass

    def midi_ch_prefix(self, channel):
        """Handle (deprecated) MIDI channel prefix event.

        :param int channel: midi channel number for subsequent data

        """
        pass

    def midi_port(self, value):
        """Handle (deprecated) MIDI port event.

        :param int value: midi port number (deprecated)

        """
        pass

    def sequence_name(self, text):
        """Handle sequence / track name event.

        In a Type-1 MIDI file, the track name event of track #0 should be interpreted as the
        name of the sequence as a whole.

        param:str:text: sequence / track name

        """
        pass

    def sequence_number(self, value):
        """Handle sequence number event.

        :param int value: sequence number (0-16383)

        """
        pass

    def sequencer_specific(self, data):
        """Handle sequencer specific event.

        :param bytes data: The data as byte values

        """
        pass

    def smtp_offset(self, hour, minute, second, frame, frame_part):
        """Handle SMTP offset event.

        :param int hour: the hour (0-23). The hour should be encoded with the SMPTE format, just as
          it is in MIDI Time Code.
        :param int minute: minutes (0-59)
        :param int second: seconds (0-59)
        :param int frame: a byte specifying the number of frames per second (one of:
            24, 25, 29, 30).
        :param int frame_part: a byte specifying the number of fractional frames, in 100ths of a
            frame (even in SMPTE-based tracks using a different frame subdivision, defined in the
            MThd chunk).

        """
        pass

    def tempo(self, value):
        """Handle tempo event.

        The tempo es given in in µs/quarternote.

        :param int value: 0-2097151

        To calculate the tempo value from bpm: ``int(60,000,000 / BPM)``

        """
        pass

    def text(self, text):
        """Handle text event.

        :param str text: arbitrary text

        """
        pass

    def time_signature(self, nn, dd, cc, bb):
        """Handle time signature event.

        :param int nn: Numerator of the signature as notated on sheet music
        :param int dd: Denominator of the signature as notated on sheet music. The denominator is a
          negative power of 2: 2 = quarter note, 3 = eighth, etc.
        :param int cc: The number of MIDI clocks in a metronome click
        :param int bb: The number of notated 32nd notes in a MIDI quarter note (24 MIDI clocks)

        """
        pass

    def unknown_meta_event(self, meta_type, data):
        """Handle any undefined meta events."""
        pass


class PrintingMidiEventHandler(NullMidiEventHandler):
    """This class reports basic information about MIDI events to standard
    output as they are encountered.

    It is mostly useful for debugging.

    """

    #########################
    ## File events

    def header(self, format=0, num_tracks=1, tick_division=96, metrical=True,
               fps=0xE7, frame_resolution=0x28):
        if metrical:
            print('format: %s, no. of tracks: %i, tick division: %i ppqn' %
                  (format, num_tracks, tick_division))
        else:
            print('format: %s, no. of tracks: %i, fps: %i, resolution: %i' %
                  (format, num_tracks, fps, frame_resolution))
        print('-' * 60)
        print('')

    def eof(self):
        print('End of file')

    def start_of_track(self, track=0):
        super(PrintingMidiEventHandler, self).start_of_track(track)
        print('Start of track #%s' % track)

    #############################
    ## Channel events

    def channel_pressure(self, channel, pressure):
        print('Channel pressure - ch:%02i, pressure=%02Xh' %
              (channel, pressure))

    def controller_change(self, channel, controller, value):
        print('Controller - ch: %02i, cont:%02Xh, value:%02Xh' %
              (channel, controller, value))

    def note_off(self, channel=0, note=0x40, velocity=0x40):
        print('Note off - ch:%02i, note:%02Xh, vel:%02Xh time:%s' %
              (channel, note, velocity, self.relative_time))

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        print('Note on - ch:%02i, note:%02Xh, vel:%02Xh time:%s' %
              (channel, note, velocity, self.relative_time))

    def pitch_bend(self, channel, value):
        print('Pitch bend - ch:%02s, value:%02Xh' % (channel, value))

    def poly_pressure(self, channel=0, note=0x40, pressure=0x40):
        print('Poly pressure - ch: %02i, note:%02Xh, pressure:%02Xh',
              (channel, note, pressure))

    def program_change(self, channel, program):
        print('Program change - ch:%02i, program:%02Xh' % (channel, program))

    def unknown_channel_message(self, status, data):
        print('Unknown channel message - status:%s, data:%r' % (status, data))

    ###############
    ## sysex event

    def system_exclusive(self, data):
        print('System exclusive message - size:%i' % (len(data) + 1))

    #####################
    ## meta events

    def copyright(self, text):
        print("Copyright - '%s'" % text.decode(self.encoding))

    def cuepoint(self, text):
        print("Cuepoint - '%s'" % text.decode(self.encoding))

    def device_name(self, text):
        print("Device name - '%s'" % text.decode(self.encoding))

    def end_of_track(self, track=None):
        print('End of track #%s' % track)
        print('')

    def instrument_name(self, text):
        print("Instrument name - '%s'" % text.decode(self.encoding))

    def key_signature(self, sf, mi):
        keys = ('Cb', 'Gb', 'Db', 'Ab', 'Eb', 'Bb', 'F',
                'C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#')
        print('Key signature - %s %s' % (keys[sf + 7], 'minor' if mi else 'major'))

    def marker(self, text):
        print("Marker - '%s'" % text.decode(self.encoding))

    def midi_ch_prefix(self, channel):
        print('MIDI channel prefix - ch:%02i' % channel)

    def midi_port(self, port):
        print('MIDI port - port:%i' % port)

    def lyric(self, text):
        print("Lyric - '%s'" % text.decode(self.encoding))

    def program_name(self, text):
        print("Program name - '%s'" % text.decode(self.encoding))

    def sequence_name(self, text):
        print("Sequence name - '%s'" % text.decode(self.encoding))

    def sequence_number(self, number):
        print('Sequence number - no.:%i' % number)

    def sequencer_specific(self, data):
        print('Sequencer specific - size:%i' % len(data))

    def smtp_offset(self, hour, minute, second, frame, framePart):
        print('SMTP offset - %02i:%02i:%02i.%i/%i' %
              (hour, minute, second, frame, framePart))

    def tempo(self, value):
        print('Tempo - val:%i (%.2f bpm)' % (value, 60000000.00 / value))

    def text(self, text):
        print("Text - '%s'" % text.decode(self.encoding))

    def time_signature(self, nn, dd, cc, bb):
        print('Time signature - %i/%i %i %i' % (nn, 2**dd, cc, bb))

    def unknown_meta_event(self, meta_type, data):
        print('Unknown meta event - type:%s, size:%i' %
              (meta_type, len(data)))
