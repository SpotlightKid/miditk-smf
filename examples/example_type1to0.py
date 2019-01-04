#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which converts a Type 1 SMF to Type 0 file."""

import logging
from operator import attrgetter
from os.path import abspath, dirname, join

from miditk.common.constants import (CUEPOINT, DEVICE_NAME, END_OF_TRACK, INSTRUMENT_NAME,
                                     KEY_SIGNATURE, MARKER, MIDI_PORT, SEQUENCE_NAME,
                                     SEQUENCE_NUMBER, SMTP_OFFSET, TEMPO, TIME_SIGNATURE)
from miditk.smf import MidiFileWriter, MidiSequence


log = logging.getLogger('miditk.smf.examples.type1to0')


# MidiFileWriter is a sub-class of NullMidiEventHandler
class Type0Converter(MidiFileWriter):
    """Write MidiSequence to a Type 0 MIDI file.

    Discards any meta events from track +1..n, which do not make sense in a type 0 file.

    """
    # These meta event types are excluded from the output if they occur on any other than track 0
    ignore_meta_events = (
        CUEPOINT,
        DEVICE_NAME,
        END_OF_TRACK,
        INSTRUMENT_NAME,
        KEY_SIGNATURE,
        MARKER,
        MIDI_PORT,
        SEQUENCE_NAME,
        SEQUENCE_NUMBER,
        SMTP_OFFSET,
        TEMPO,
        TIME_SIGNATURE
    )

    def write(self, sequence):
        log.debug("Writing Type 0 file header.")
        self.header(format=0, num_tracks=1, tick_division=sequence.tick_division,
                    metrical=sequence.metrical, fps=sequence.fps,
                    frame_resolution=sequence.frame_resolution)
        log.debug("Starting track #0.")
        self.start_of_track(0)

        for ticks, events in sequence.events_by_ticks():
            log.debug("Current Tick: %i", ticks)
            self.update_ticks(ticks, relative=False)

            # loop over events for this tick in reverse order of their type code,
            # i.e. meta events will come first, then sysex/escape-sequences, then
            # program/controller changes/pitchbend/aftertouch, then note data.
            for event in sorted(events, key=attrgetter('type'), reverse=True):
                # Ignore all "end of track" meta events,
                # we will add the one for track #0 later.
                if event.meta_type == END_OF_TRACK:
                    continue

                # Ignore meta events from track #0..n, which do not make sense in a Type 0 file.
                if event.track != 0 and event.meta_type in self.ignore_meta_events:
                    log.warning("Discarding event: %r", event)
                    continue

                log.debug("Writing event to track #0: %r", event)
                self.event_slice(event.to_bytes())

        log.debug("Writing end-of-track event to track #0 and writing track.")
        self.end_of_track(0)
        self.eof()


if __name__ == '__main__':
    import sys
    from os.path import splitext

    if '-v' in sys.argv[1:]:
        loglevel = logging.DEBUG
        sys.argv.remove('-v')
    else:
        loglevel = logging.INFO

    logging.basicConfig(level=loglevel)

    parentdir = dirname(dirname(abspath(__file__)))

    if len(sys.argv[1:]) >= 1:
        infilename = sys.argv[1]

        if len(sys.argv[1:]) >= 2:
            outfilename = sys.argv[2]
        else:
            outfilename = splitext(infilename)[0] + '-type0.mid'
    else:
        # Use test file if no input file is given on the command line.
        # This is a small type 1 midi file, with only two midi events on track #1
        # and "sequence name" meta events on all 17 tracks.
        infilename = join(parentdir, 'tests', 'testdata', 'minimal-cubase-type1.mid')
        # The output is written to the tests/testoutput directory
        outfilename = join(parentdir, 'tests', 'testoutput', 'type0-converted.mid')

    # Parse input file to a MidiSequence
    with open(infilename, 'rb') as insmf:
        seq = MidiSequence.fromfile(insmf)

    with open(outfilename, 'wb') as outsmf:
        midiout = Type0Converter(outsmf)
        # now do the processing
        midiout.write(seq)
