#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Map note values of all note on/off events according to given mapping file."""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import csv
import logging
import sys

from os.path import splitext

from miditk.smf import MidiFileReader, MidiFileWriter


log = logging.getLogger("note_remapper")


class NoteRemapper(MidiFileWriter):
    """Map note values of all note on/off events according to given mapping file.
    """
    def __init__(self, fp, mapfn, channel=0, encoding='UTF-8', convert_zero_velocity=False):
        super(NoteRemapper, self).__init__(fp, encoding=encoding)
        self._map = self.read_mapping(mapfn)
        self.channel = channel
        self.convert_zero_velocity = convert_zero_velocity

    def read_mapping(self, mapfn):
        notemap = {}
        with open(mapfn, newline='') as csvfile:
            sample = csvfile.read(1024)
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            csvfile.seek(0)
            reader = csv.reader(csvfile, dialect)

            for lineno, row in enumerate(reader):
                if lineno == 0 and sniffer.has_header(sample):
                    continue

                if len(row) > 2 and row[1].strip():
                    try:
                        srcnote, destnote = int(row[0]), int(row[1])

                        if any((0 > srcnote > 127, 0 > destnote > 127)):
                            raise ValueError("Note number out of range (0 - 127)")
                    except (TypeError, ValueError) as exc:
                        log.warning("Error in mapping file on line %i: %s", lineno, exc)
                    else:
                        notemap[srcnote] = destnote

        return notemap

    def map_note(self, ch, note):
        if self.channel in (0, ch + 1):
            note = max(0, min(127, self._map.get(note, note)))
        return note

    def note_on(self, channel=0, note=0x40, velocity=0x40):
        note = self.map_note(channel, note)
        super(NoteRemapper, self).note_on(channel, note, velocity)

    def note_off(self, channel=0, note=0x40, velocity=0x40):
        note = self.map_note(channel, note)
        super(NoteRemapper, self).note_off(channel, note, velocity)


def main(args=None):
    ap = argparse.ArgumentParser(description=__doc__)
    padd = ap.add_argument
    padd('-v', '--verbose', action="store_true",
         help='verbose output')
    padd('-c', '--channel', metavar="CH", type=int, default=0,
         help='MIDI channel to apply mapping to (default: 0 => all channels)')
    padd(dest='mapfile',
         help='Note mapping file name (CSV format).')
    padd(dest='infile',
         help='Input file name (Standard MIDI File format).')
    padd(dest='outfile', nargs="?",
         help="Output file name (default: add '_remapped' to input file name).")

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    logging.basicConfig(format="%(name)s: %(levelname)s - %(message)s",
                        level=logging.DEBUG if args.verbose else logging.INFO)

    if args.outfile:
        outfile = args.outfile
    else:
        fn, ext = splitext(args.infile)
        outfile = fn + '_remapped' + ext

    # create event handlers
    with open(outfile, 'wb') as smf:
        midiout = NoteRemapper(smf, args.mapfile, channel=args.channel)
        midiin = MidiFileReader(args.infile, midiout)

        # now do the processing
        midiin.read()


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
