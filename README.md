# miditk-smf

A Python toolkit for working with Standard MIDI files

## Quickstart

Install:

```console
pip install miditk-smf
```

Usage:

```py
from miditk.smf import MidiFileWriter

# Open file for writing in binary mode.
with open('minimal.mid', 'wb') as smf:
    # Create standard MIDI file writer.
    midi = MidiFileWriter(smf)

    # Write file and track header for Type 0 file, one track, 96 pulses per
    # quarter note (ppqn). These are also the default parameter values.
    midi.header(format=0, num_tracks=1, tick_division=96)
    midi.start_of_track()

    # Set tempo to 120 bpm in µsec per quarter note.
    # When no tempo is set in the MIDI file, sequencers will generally assume
    # it to be 120 bpm.
    midi.tempo(int(60_000_000 / 120))

    # Add MIDI events.
    midi.note_on(channel=0, note=0x40)
    # Advance 192 ticks (i.e. a half note).
    midi.update_ticks(192)
    midi.note_off(channel=0, note=0x40)

    # End track and midi file.
    midi.end_of_track()
    midi.eof()
```

For more examples, see the [Usage examples](#usage-examples) section below.


## Overview

`miditk-smf` is a general-purpose library for the parsing and generation of
Standard MIDI Files (SMF). The package is part of several planned packages
under the common top-level package namespace `miditk`. This package mainly
provides the `miditk.smf` sub-package for handling standard MIDI files.
Additional sub-packages with more specialised MIDI libraries and tools may be
developed and distributed as separate package distributions in the future.


### Compatibility

`miditk-smf` works with (C)Python >= 3.7 and PyPy 3.


## Installation

`miditk-smf` is installable via [pip](https://pypi.org/project/pip/)
from the [Python Package Index](https://pypi.org/project/miditk-smf/):

```console
pip install miditk-smf
```

It is provided as a source distribution and a universal Python wheel for all
supported Python versions and operating systems. It only depends on the Python
standard library.


## Package contents

`miditk.common`:

A collection of constants from the MIDI specification used by sub-packages and
general data types for working with MIDI events.

`miditk.smf`:

An event-based standard MIDI file (SMF) parsing and generation framework.

`miditk.smf.api`:

Base event handler classes, which can be subclassed for specialised event
handling.

`miditk.smf.converters`:

A collection of functions that converts the special data types used in midi
files to and from byte strings.

`miditk.smf.parser`:

The main binary MIDI file data parser.

`miditk.smf.reader`:

Combines the parser with an event handler class.

`miditk.smf.sequence`:

An event handler, which stores all MIDI events from a MIDI file in a
`MidiSequence` container class.

`miditk.smf.writer`:

An event handler to write out MIDI events to a standard MIDI File.


## Usage examples

The following section contains a few code examples, which demonstrate several
usage scenarios for the different modules in the package. For more examples see
also the scripts in the [examples] directory of the source distribution.


### Parsing a standard MIDI file

The `miditk.smf` module provides the `MidiSequence` container class, which uses
its own MIDI event handler class to collect all information and events from
parsing a midi file. Use the `MidiSequence.fromfile()` class method to parse a
standard MIDI file.

You can then use several convenience methods of the returned `MidiSequence`
instance to access information about the midi file properties or events.

```py
from miditk.smf import MidiSequence

# Do parsing
sequence = MidiSequence.fromfile(sys.argv[1])

# Print some info from the MIDI file header,
# e.g. number of tracks, events sequence name.
print(sequence)
# Print a list of events with event type, data and timestamp.
sequence.dump_events()

# Iterate over all sysex events in track 0.
# If track is not specified, sysex_events() yields all sysex events
# in all tracks.
for ev in sequence.sysex_events(track=0):
    print("Sysex event ({} bytes) @ {:.2f}".format(len(ev.data), ev.timestamp))

# Iterate over all events sorted by timestamp and then track.
for time, group in sequence.events_by_time():
    for ev in group:
        handle_event(ev)
```


### Changing MIDI events in-stream

The event-based parsing allows to handle MIDI events as they are read (or
received via MIDI in). You need to define a sub-class of
`miditk.smf.BaseMidiEventHandler` or `miditk.smf.NullMidiEventHandler` and
overwrite only the event handling methods for the events you are interested in.

The following example transposes all note on/off events by an octave (i.e. 12
semitones):

```py
import sys
from miditk.smf import MidiFileReader, MidiFileWriter

# MidiFileWriter is a sub-class of NullMidiEventHandler.
class Transposer(MidiFileWriter):
    """Transpose note values of all note on/off events by 1 octave."""

    def note_on(self, channel, note, velocity):
        super().note_on(self, channel, min(127, note + 12), velocity)

    def note_off(self, channel, note, velocity):
        super().note_off(self, channel, min(127, note + 12), velocity)

infile = sys.argv.pop(1)
outfile = sys.argv.pop(1)

# Create the parser and event handler
with open(outfile, 'wb') as smf:
    midiout = Transposer(smf)
    midiin = MidiFileReader(infile, midiout)

    # Now do the processing.
    midiin.read()
```


## Development

Clone the Git repository:

```console
git clone https://github.com/SpotlightKid/miditk-smf.git
cd miditk-smf
```

Install tox:

```console
pip install tox
```

Or via your Linux distribution package manager, e.g. on debian/Ubuntu:

```console
sudo apt-get install python-tox
```

Or on Arch Linux:

```console
sudo pacman -S python-tox
```

Run the tests via tox for all Python versions configured in `tox.ini`:

```console
tox
```

If all is well, create a new git branch and start hacking and then contribute
your changes by opening a [pull
request](https://github.com/SpotlightKid/miditk-smf/pulls) on GitHub.


## Code QA

The included Makefile is set up to run several Python static code checking and
reporting tools. To print a list of available Makefile targets and the tools
they run, simple run:

```console
make
```

Then run the Makefile target of your choice, e.g.:

```console
make flake8
```

Unless noted otherwise, these targets run all tools directly, i.e. without tox,
which means they need to be installed in your Python environment. You can use
[hatch] to create a virtual environments for general development tasks or for
specific tasks as, for example, building the documentation. Dependencies and
tools needed for these tasks will be installed automatically into these
environments on creation:

To show which special environments are defined:

```console
hatch env show
```

To create and enter e.g. the "dev" environment:

```console
hatch --env dev shell
```


## Documentation

Package documentation is generated by Sphinx. The documentation can be build
with:

```console
make docs
```

After a successful build the documentation index is opened in your web
browser.


## Authors and License

The `miditk` package is written by Christopher Arndt and licensed under the MIT
License.

The the structure of the `miditk.smf` sub-package owes inspiration to the
[Python Midi] [^1] package, written by <maxm@maxm.dk>.


[examples]: https://github.com/SpotlightKid/miditk-smf/tree/master/examples
[python midi]: http://web.archive.org/web/20100919095628/http://www.mxm.dk/products/public/pythonmidi/
[^1]: Original web site, now defunct: http://www.mxm.dk/products/public/pythonmidi/
