#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which prints all note on events on MIDI channel 0."""

import sys

from os.path import abspath, dirname, join

from miditk.smf import MidiFileReader, NullMidiEventHandler


class ChannelZeroPrinter(NullMidiEventHandler):
    """This prints all note on/off events on MIDI channel 0."""

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        if channel == 0:
            print(channel, note, velocity, self.relative_time)

    note_off = note_on


try:
    infile = sys.argv[1]
except IndexError:
    infile = join(dirname(dirname(abspath(__file__))), 'tests', 'testdata',
                  'minimal-cubase-type1.mid')

# create the reader and the event handler
midiin = MidiFileReader(infile, handler=ChannelZeroPrinter())
# do parsing
midiin.read()
