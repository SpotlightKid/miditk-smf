#!/usr/bin/env python3
"""Write MIDI file with the following events:

format: 0, # of tracks: 1, division: 480
----------------------------------

Start of track #0
Sequence name - 'Type 0'
Tempo: val:500000 (125.0 bpm)
Time signature: 4/4 24 8
Note on - ch:00, note:48h, vel:64h time:0
Note off - ch:00, note:48h, vel:40h time:480
End of track
End of file

"""

import io
import os
from os.path import dirname, isdir, join

import pytest  # noqa

from miditk.smf.writer import MidiFileWriter


def test_write_type0():
    cmpfn = join(dirname(__file__), 'testdata', 'midiout.mid')
    outdir = join(dirname(__file__), 'testoutput')
    outfn = join(outdir, 'midiout.mid')

    if not isdir(outdir):
        os.makedirs(outdir)

    with open(outfn, 'wb') as smf:
        midi = MidiFileWriter(smf)

        midi.header(0, 1, 480)

        midi.start_of_track()
        midi.sequence_name('Type 0')
        midi.tempo(750000)
        midi.time_signature(4, 2, 24, 8)
        ch = 0

        for i in range(127):
            midi.note_on(ch, i, 0x64)
            midi.update_ticks(96)
            midi.note_off(ch, i, 0x40)
            midi.update_ticks(0)

        midi.update_ticks(0)
        midi.end_of_track()
        midi.eof()

    with open(outfn, 'rb') as out, open(cmpfn, 'rb') as cmp:
        assert cmp.read() == out.read()


def test_write_sysex_issue_7():
    smf = io.BytesIO()
    midi = MidiFileWriter(smf)
    midi.header(format=0, num_tracks=1, tick_division=96)
    midi.start_of_track(track=0)
    midi.system_exclusive(b'\xF0\xFD\x01\x02\x03\xF7')
    midi.end_of_track()
    midi.eof()

    assert b'\xf0\x07\xf0\xfd\x01\x02\x03\xf7' in smf.getvalue()
