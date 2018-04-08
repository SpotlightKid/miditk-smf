miditk-smf
##########

A toolkit for working with Standard MIDI files


Quickstart
==========

Clone the repo::

    $ git clone https://github.com/SpotlightKid/miditk-smf.git
    $ cd miditk-smf

Install tox::

    $ sudo apt-get install python-tox

Run the tests via tox for all Python versions configured in `tox.ini`::

    $ tox

If all is well, continue to the `Usage examples`_ section below.


Overview
========

``miditk-smf`` is a general-purpose library for the parsing and generation of
Standard MIDI Files (SMF). The package is part of several packages under the
common top-level package namespace ``miditk``. This package mainly provides
the ``midi.smf`` sub-package for handling standard MIDI files. Additional
sub-packages with more specialised MIDI libraries and tools will be distributed
as separate package distributions in the future.


Compatibility
-------------

``miditk-smf`` works with Python 2.7, Python 3.4+ and PyPy 2 and 3.


Installation
============

``miditk-smf`` is installable via pip_ from the `Python Package Index`_:

    $ pip install miditk-smf

It is provided as a source distribution and as Python wheels for different
Python versions and operating systems.


Package contents
================

``miditk.common``
    A collection of constants from the MIDI specification used by sub-packages
    and general data types for working with MIDI events.

``miditk.smf``
    An event-based standard MIDI file (SMF) parsing and generation framework.

``miditk.smf.api``
    Base event handler classes, which can be sublassed for specialised event
    handling.

``miditk.smf.converters``
    A collection of functions that converts the special data types used in midi
    files to and from byte strings.

``miditk.smf.parser``
    The main binary MIDI file data parser.

``miditk.smf.reader``
    Combines the parser with an event handler class.

``miditk.smf.sequence``
    An event handler, which stores all MIDI events from a MIDI file in a
    MidiSequence container class.

``miditk.smf.sequence``
    An event handler to write out MIDI events to a Standard MIDI File.


.. _usage examples:

Usage examples
==============

The following section contains a few code examples, which demonstrate several
usage scenarios for the different modules in the package. For more examples see
also the scripts in the ``examples`` directory of the source distribution.


Parsing a standard MIDI file
----------------------------

The ``miditk.smf`` module provides the ``MidiSequence`` container class, which
uses its own MIDI event handler class to collect all information and events
from parsing a midi file. Use the ``MidiSequence.fromfile()`` class method to
parse a standard MIDI file.

You can then use several convenience methods of the returned ``MidiSequence``
instance to access information about the midi file properties or events.

::

    from miditk.smf import MidiSequence

    # do parsing
    sequence = MidiSequence.fromfile(sys.argv[1])

    # print some info from the MIDI file header,
    # e.g. number of tracks, events sequence name
    print(sequence)
    # print a list of events with event type, data and timestamp
    sequence.dump_events()

    # iterate over all sysex events in track 0
    # if track is not specified, sysex_events() yields all sysex events
    # in all tracks
    for ev in sequence.sysex_events(track=0):
        print "Sysex event (%i bytes) @ %.2f" (len(ev.data), ev.timestamp)

    # iterate over all events sorted by timestamp and then track
    for ev in sequence.events_by_time():
        handle_event(ev)


Changing MIDI events in-stream
------------------------------

The event-based parsing allows to handle MIDI events as they are read (or
received via MIDI in). You need to define a sub-class of
``miditk.smf.BaseMidiEventHandler`` or ``miditk.smf.NullMidiEventHandler``
and overwrite only the event handling methods for the events you are
interested in.

The following example transposes all note on/off events by an octave
(i.e. 12 semitones)::

    from miditk.smf import MidiFileReader, MidiFileWriter

    # MidiFileWriter is a sub-class of NullMidiEventHandler
    class Transposer(MidiFileWriter):
        """Transpose note values of all note on/off events by 1 octave."""

        def note_on(self, channel=0, note=60, vel=64):
            super().note_on(self, channel, min(127, note + 12), vel)

        def note_off(self, channel=0, note=60, vel=64):
            super().note_off(self, channel, min(127, note + 12), vel)

    infile = sys.argv.pop(1)
    outfile = sys.argv.pop(1)

    # create event handlers
    midiout = Transposer(outfile)
    midiin = MidiFileReader(infile, midiout)

    # now do the processing
    midiin.read()


Code QA
=======

The included Makefile is set up to run several Python static code checking and
reporting tools. To print a list of available Makefile targets and the tools
they run, simple run::

    $ make

Then run the Makefile target of your choice, e.g.::

    $ make flake8

Unless noted otherwise, these targets run all tools directly, i.e. without tox,
which means they need to be installed in your Python environment, preferably in
a project-specific virtual environment. To create a virtual environment and
install all supported tools and their dependencies run::

    $ mkvirtualenv miditk-smf
    (miditk-smf)$ pip install -r requirements/dev.txt


Documentation
=============

Package documentation is generated by Sphinx. The documentation can be build
with::

    $ make docs

After a successful build the documentation index is opened in your web browser.


Authors and License
===================

The ``miditk`` package is written by Christopher Arndt and licensed under the
MIT License.

The the structure of the ``miditk.smf`` sub-package ows inspiration to the
`python midi package`_, written by maxm@maxm.dk.


.. _python midi package: http://www.mxm.dk/products/public/pythonmidi/
.. _python package index: http://pypi.python.org/pypi/miditk-smf
.. _pip: http://pypi.python.org/pypi/pip
