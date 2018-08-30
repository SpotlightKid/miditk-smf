#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example script which maps program change numbers."""

from miditk.smf import MidiFileReader, MidiFileWriter


class ProgramChangeMapper(MidiFileWriter):
    """Change program number of Program Change events according to given mapping."""

    def __init__(self, outfile, pcmap, channel=None, track=None):
        self.pcmap = pcmap
        self.channel = (channel,) if isinstance(channel, int) else channel
        self.track = (track,) if isinstance(track, int) else track
        super().__init__(outfile)

    def program_change(self, channel, program):
        if ((self.channel is None or channel in self.channel) and
                (self.track is None or self.current_track in self.track)):
            program = self.pcmap.get(program, program)
        super().program_change(self, channel, min(127, max(0, program)))


if __name__ == '__main__':
    import sys
    infilename = sys.argv.pop(1)
    outfilename = sys.argv.pop(1)
    # Program change mapping
    pcmap = {
        0: 40,   # Ac. Piano -> Strings
        32: 33,  # Ac. Bass -> Electric Bass
    }
    # Create parser and event handler
    with open(outfilename, 'wb') as smf:
        midiout = ProgramChangeMapper(smf, pcmap)
        midiin = MidiFileReader(infilename, handler=midiout)
        # Now do the processing.
        midiin.read()
