# -*- coding:utf-8 -*-

from __future__ import print_function, unicode_literals

import sys
from io import StringIO
from os.path import dirname, join

import pytest  # noqa

from miditk.smf.api import PrintingMidiEventHandler
from miditk.smf.reader import MidiFileReader


def test_minimal_type0():
    """Test that we get the right output for a minimal type 0 midi test file."""
    test_file = join(dirname(__file__), 'testdata', 'minimal-cubase-type0.mid')

    # Do parsing, and generate events with MidiToText, so we can see what a
    # minimal midi file contains:

    midi_in = MidiFileReader(test_file, PrintingMidiEventHandler())
    old_stdout = sys.stdout
    capture_stdout = StringIO()
    sys.stdout = capture_stdout
    midi_in.read()
    result = capture_stdout.getvalue()
    sys.stdout = old_stdout
    assert result.strip() == """\
format: 0, no. of tracks: 1, tick division: 480 ppqn
------------------------------------------------------------

Start of track #0
Sequence name - 'Type 0'
Tempo - val:500000 (120.00 bpm)
Time signature - 4/4 24 8
Note on - ch:00, note:48h, vel:64h time:0
Note off - ch:00, note:48h, vel:40h time:480
End of track #0

End of file"""
