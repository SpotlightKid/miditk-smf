#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which creates the smallest possible type 0 midi file.

All the midi events are in the same track chunk, which only contains one note
on and off event.

"""

import sys
from os.path import abspath, dirname, join

from miditk.smf import MidiFileWriter


try:
    outfile = sys.argv[1]
except IndexError:
    outfile = join(dirname(dirname(abspath(__file__))), 'tests', 'testoutput', 'minimal-type0.mid')

with open(outfile, 'wb') as smf:
    midi = MidiFileWriter(smf)

    # write file and track header
    midi.header()
    midi.start_of_track()

    # musical events
    midi.note_on(channel=0, note=0x40)

    midi.update_ticks(192)
    midi.note_off(channel=0, note=0x40)

    # end track and midi file
    midi.end_of_track()
    midi.eof()
