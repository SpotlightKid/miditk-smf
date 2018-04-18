#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which transposes all note on/off event by one octave."""

from os.path import abspath, dirname, join
from miditk.smf import MidiFileReader, MidiFileWriter


# MidiFileWriter is a sub-class of NullMidiEventHandler
class Transposer(MidiFileWriter):
    """Transpose note values of all note on/off events by 1 octave."""

    def _transp(self, ch, note):
        # don't transpose note son teh drum channel
        if ch != 9:
            note = min(127, note + 12)

        return note

    def note_on(self, channel, note, velocity):
        note = self._transp(channel, note)
        super(Transposer, self).note_on(channel, note, velocity)

    def note_off(self, channel, note, velocity):
        note = self._transp(channel, note)
        super(Transposer, self).note_off(channel, note, velocity)


# This is a small type 0 midi file, with only two midi events on track #0.
infile = join(dirname(dirname(abspath(__file__))), 'tests', 'testdata', 'minimal.mid')
# The output is written to the tests/testoutput directory
outfile = join(dirname(dirname(abspath(__file__))), 'tests', 'testoutput', 'transposed.mid')

# create parsre and event handler
with open(outfile, 'wb') as smf:
    midiout = Transposer(smf)
    midiin = MidiFileReader(infile, midiout)
    # now do the processing
    midiin.read()
