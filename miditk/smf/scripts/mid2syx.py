#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# midi2syx.py
#
"""Extract all system excusive messages from a standard MIDI file.

By default writes each sysex event contained in the MIDI file to its own file
in the output directory (defaults to the current working directory) which
contains the pure sysex data. The filename of each sysex file is constructed
by appending the number of the sysex event to a common prefix, which can be
specified via an option (defaults to `msg_`).

"""

from __future__ import print_function

import logging
import argparse
import os
import sys

from miditk.common.constants import SYSTEM_EXCLUSIVE
from miditk.smf import MidiSequence


__version__ = "0.2"
__usage__ = "Usage: mid2syx.py MIDIFILE"


def _ord(x):
    return x if isinstance(x, int) else ord(x)


def error(msg, *args):
    print(msg % args, stream=sys.stderr)


def checksum(msg, data_offset):
    return sum(_ord(c) for c in msg[data_offset:-2]) & 0x7f


def sysex_info(msg, msg_no):
    if _ord(msg[0]) == 0:
        manufacturer_id = '%Xh %Xh' % (_ord(msg[1]), _ord(msg[2]))
        model_id = _ord(msg[3])
        device_id = _ord(msg[4])
    else:
        manufacturer_id = '%Xh' % _ord(msg[0])
        model_id = _ord(msg[2])
        device_id = _ord(msg[3])

    return ("Msg #%03i, %i bytes, manufacturer: %s, model: %03Xh, device ID %03Xh" %
            (msg_no, len(msg) + 1, manufacturer_id, model_id, device_id))


def main(args=None):
    ap = argparse.ArgumentParser(usage=__usage__, description=__doc__)
    aa = ap.add_argument
    aa('-c', '--checksum', action="store_true", help="Verify check sum of each sysex message.")
    aa('-n', '--dry-run', action="store_true",
       help="Only print what would be done, do not write any files.")
    aa('-p', '--prefix', metavar="PREFIX", default="msg_",
       help="Filename prefix for each sysex file.")
    aa('-o', '--output-dir', metavar="DIR", default=os.getcwd(),
       help="Output directory where extracted sysex files will be written.")
    aa('-q', '--quiet', action="store_true",
       help="Do not print anything to standard output at all.")
    aa('-v', '--verbose', action="store_true",
       help="Print debugging info to standard output.")
    aa('midifile', metavar="MIDIFILE",
       help="Standard MIDI input file.")
    aa('--version', action='version', version="mid2sys " + __version__)

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING)

    if not os.path.isdir(args.output_dir):
        error("Not a directory: '%s'\n", args.output_dir)
        ap.print_help()
        return 1

    sequence = MidiSequence.fromfile(args.midifile)

    for i, ev in enumerate(sequence.sysex_events()):
        assert ev.type == SYSTEM_EXCLUSIVE
        assert _ord(ev.data[0]) < 127
        assert ev.data.endswith(b'\xF7')

        if not args.quiet:
            print("Track #%02i: %s" % (ev.track + 1, sysex_info(ev.data, i + 1)))

        if args.checksum:
            cs = checksum(ev.data, 6)
            if cs != _ord(ev.data[-2]):
                error("Checksum verification for msg #%03i failed! "
                      "Expected %i, read %i", i + 1, cs, _ord(ev.data[-2]))

        outfile = os.path.join(args.output_dir, "%s%03i.syx" % (args.prefix, i + 1))

        try:
            if not args.dry_run:
                fp = open(outfile.encode('utf-8'), 'wb')
        except (IOError, OSError) as exc:
            error("Could not open output file '%s' for writing.", outfile)
        else:
            if args.verbose:
                print("Writing sysex msg #%03i to '%s'..." % (i + 1, outfile))
            if not args.dry_run:
                fp.write(b"\xF0" + ev.data)
                fp.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
