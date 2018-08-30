#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which creates a type 0 midi file with a simple drum 4/4 pattern.

All midi events are in the same track chunk on channel 9 (the midi channel
reserved for drums in the General Midi standard).

"""

import sys
from os.path import abspath, dirname, join

from miditk.smf import MidiFileWriter


try:
    outfilename = sys.argv[1]
except IndexError:
    parentdir = dirname(dirname(abspath(__file__)))
    outfilename = join(parentdir, 'tests', 'testoutput', 'drumpattern.mid')

with open(outfilename, 'wb') as smf:
    midi = MidiFileWriter(smf)

    # write file and track header
    midi.header()
    midi.start_of_track()

    # set tempo to 120 bpm
    midi.tempo(int(60000000 / 120))

    # musical events
    # Let's play two bars
    for i in range(4):
        # Acoustic Bass Drum on first/third beat
        midi.note_on(channel=9, note=35)
        # Closed Hi-Hat
        midi.note_on(channel=9, note=42)

        # step one eigth note
        midi.update_ticks(48)
        # Hi-Hat
        midi.note_on(channel=9, note=42)

        # step one eigth note
        midi.update_ticks(48)
        # Acoustic Snare on second/fourth quaver
        midi.note_on(channel=9, note=38)
        # Hi-Hat
        midi.note_on(channel=9, note=42)

        # step one eigth note
        midi.update_ticks(48)
        # Hi-Hat
        midi.note_on(channel=9, note=42)

        # step one eigth note
        midi.update_ticks(48)

    # end track and midi file
    midi.end_of_track()
    midi.eof()
