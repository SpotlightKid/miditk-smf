Changelog
#########


0.2.2 (2019-01-04)
==================

* Added example script to convert a type 1 MIDI file into a type 0 format file.
* Moved previously private ``MidiEvent`` class to ``miditk.smf.api`` module and
  exposed it in ``miditk.smf`` module name space and improved and fixed several
  aspects of the ``MidiEvent`` class.
* Fixed parsing of polyphonic pressure events.
* Fixed output for polyphonic pressure events in ``PrintingMidiEventHandler``.
* Fix time keeping in ``ObjectMidiEventHandler`` for multi-track files:
  reset ``current_time`` attribute when new track starts.
* Fixed: ``BaseMidiEventHandler`` used wrong handler method name for sysex messages.
* Updated base/dev requirements.


0.2.1 (2018-08-20)
==================

* Fixed missing string formatting args in ``PrintingMidiEventHandler.key_signature`` method.
* Added ``example_program_change_map.py`` script to examples.
* Ensure support for Pyton 3.7.


0.2.0 (2018-04-18)
==================

* Removed Cython version of ``miditk.smf.converters`` module (``miditk.smf._speedups``).
  ``miditk-smf`` now only requires ``six``.
* Fixed ``tox.ini`` to work on Windows too.
* Improved and updated readme file.


0.1.0 (2018-04-09)
==================

Initial release
