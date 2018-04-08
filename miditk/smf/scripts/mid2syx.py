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
specified via an option (defaults to ``'msg_'``).

"""

from __future__ import print_function

import logging
import optparse
import os
import sys

from miditk.common.constants import SYSTEM_EXCLUSIVE
from miditk.smf import MidiSequence


__version__ = "0.2"
__usage__ = "Usage: mid2syx.py MIDIFILE"


def error(msg, *args):
    print(msg % args, stream=sys.stderr)


def checksum(msg, data_offset):
    return sum(ord(c) for c in msg[data_offset:-2]) & 0x7f


def sysex_info(msg, msg_no):
    if ord(msg[0]) == 0:
        manufacturer_id = '%Xh %Xh' % (ord(msg[1]), ord(msg[2]))
        model_id = ord(msg[3])
        device_id = ord(msg[4])
    else:
        manufacturer_id = '%Xh' % ord(msg[0])
        model_id = ord(msg[2])
        device_id = ord(msg[3])

    return ("Msg #%03i, %i bytes, manufacturer: %s, model: %03Xh, device ID %03Xh" %
            (msg_no, len(msg) + 1, manufacturer_id, model_id, device_id))


def main(args=None):
    op = optparse.OptionParser(usage=__usage__, description=__doc__, version=__version__)
    op.add_option('-c', '--checksum', action="store_true", dest="checksum",
                  help="Verify check sum of each sysex message.")
    op.add_option('-n', '--dry-run', action="store_true", dest="dryrun",
                  help="Only print what would be done, do not write any files.")
    op.add_option('-p', '--prefix', metavar="PREFIX", dest="prefix", default="msg_",
                  help="Filename prefix for each sysex file.")
    op.add_option('-o', '--output-dir', metavar="DIR", dest="outdir", default=os.getcwd(),
                  help="Output directory where extracted sysex files will be written.")
    op.add_option('-q', '--quiet', action="store_true", dest="quiet",
                  help="Do not print anything to standard output at all.")
    op.add_option('-v', '--verbose', action="store_true", dest="verbose",
                  help="Print debugging info to standard output.")

    if args is None:
        options, args = op.parse_args(args)
    else:
        options, args = op.parse_args()

    logging.basicConfig(level=logging.DEBUG if options.verbose else logging.WARNING)

    try:
        midifile = args.pop(0)
    except IndexError:
        op.print_help()
        return 2

    if not os.path.isdir(options.outdir):
        error("Not a directory: '%s'\n", options.outdir)
        op.print_help()
        return 1

    sequence = MidiSequence.fromfile(midifile)

    for i, ev in enumerate(sequence.sysex_events()):
        assert ev.type == SYSTEM_EXCLUSIVE
        assert ord(ev.data[0]) < 127
        assert ev.data.endswith('\xF7')

        if not options.quiet:
            print("Track #%02i: %s" % (ev.track + 1, sysex_info(ev.data, i + 1)))

        if options.checksum:
            cs = checksum(ev.data, 6)
            if cs != ord(ev.data[-2]):
                error("Checksum verification for msg #%03i failed! "
                      "Expected %i, read %i", i + 1, cs, ord(ev.data[-2]))

        outfile = os.path.join(options.outdir, "%s%03i.syx" % (options.prefix, i + 1))

        try:
            if not options.dryrun:
                fp = open(outfile.encode('utf-8'), 'wb')
        except (IOError, OSError) as exc:
            error("Could not open output file '%s' for writing.", outfile)
        else:
            if options.verbose:
                print("Writing sysex msg #%03i to '%s'..." % (i + 1, outfile))
            if not options.dryrun:
                fp.write("\xF0" + ev.data)
                fp.close()

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)
