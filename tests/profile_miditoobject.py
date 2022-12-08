#!/usr/bin/env python3
#
# profile_miditoobject.py
#

import sys
import cProfile

from miditk.smf.sequence import MidiSequence  # noqa:F401


if len(sys.argv) < 2:
    print("Usage: profile_miditoobject.py MIDIFILE")
else:
    filename = sys.argv.pop(1)

    if len(sys.argv) > 1:
        cProfile.run("MidiSequence.fromfile(filename)", sys.argv[1], sort='tottime')
    else:
        cProfile.run("MidiSequence.fromfile(filename)", sort='tottime')
