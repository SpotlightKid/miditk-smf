#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which uses the PrintingMidiEventHandler.

When an event is passed to this handler, it prints information about the event to the console.

The events are passed to the handler by the MidiFileReader instance.

This script prints all the events from the infile to the console, which is useful for
debugging.

"""

import sys
from os.path import abspath, dirname, join

from miditk.smf import MidiFileReader
from miditk.smf.api import PrintingMidiEventHandler


try:
    infile = sys.argv[1]
except IndexError:
    infile = join(dirname(dirname(abspath(__file__))), 'tests', 'testdata',
                  'minimal-cubase-type0.mid')

# create the reader and the event handler
midiin = MidiFileReader(infile, PrintingMidiEventHandler())
# do parsing
midiin.read()
