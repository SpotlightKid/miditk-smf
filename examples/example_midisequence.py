#!/usr/bin/env python
"""Parse a standard MIDI file into a MidiSequence instance

MidiSequence is a container for a sequence of timed MidiEvent instances,
which offers several convenience methods to access information about the
MIDI file properties and events.

"""

import sys

from miditk.smf import MidiSequence


# Do parsing
sequence = MidiSequence.fromfile(sys.argv[1])

# Print some info from the MIDI file header,
# e.g. number of tracks, events sequence name.
print("Sequence: ", sequence)


# Print a list of events with event type, data and timestamp
print("Sequence dump:")
sequence.dump_events()


# Iterate over all sysex events in track 0.
# If track is not specified, sysex_events() yields all sysex events
# in all tracks.
print("Sysex msgs in all tracks:")
for ev in sequence.sysex_events(track=0):
    print("Sysex event (%i bytes) @ %.2f" % (len(ev.data), ev.timestamp))


print("Print events sorted by timestamp:")
# Iterate over all events sorted by timestamp and then track
for time, group in sequence.events_by_time():
    print("@%.2f:" % time)
    for ev in group:
        print("%02X %s" % (ev.type, " ".join("%02X" % b for b in ev.data)))
