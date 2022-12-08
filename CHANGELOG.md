# Changelog

## 0.3.0 (2022-12-08)

Project updates:

-   Switched from `setuptools` to PEP-517-compatible build setup using
    `hatchling`.
-   Removed Python 2 support (now requires Python >= 3.7).
-   Removed `six` dependency.
-   Removed requirements files.
-   Converted README, LICENSE and CHANGELOG to Markdown format.
-   Added automatic testing and deployment of source distribution and
    wheel to PyPI via GitHub actions.

Changes:

-   Made `track` argument to `BaseMidiEventHandler.start_of_track` optional.
-   Split `MidiFileWriter` into base class and event handler sub-class.
    Base class handles event serialization and output.
-   `MidiSequence` instances now save tempo and time/key signature events.
-   `MidiSequence.fromfile` can now accept a custom handler class/instance.
-   Added command-line script `miditk-mid2syx`.
-   Updated examples and removed Python 2 compatibility idioms.

Fixes:

-   Fixed writing sysex message events in `MidiFileWriter` (#7).
-   Removed unused `dispatch_controllers` attribute in `BaseMidiEventHandler`.
-   Fixed `MidiSequence` example in readme and added example script.
-   Minor fixes: removed unused import; added geany project file to git ignores;
    fixed code formatting issues.
-   Reformated code with `black` and `isort`.

## 0.2.2 (2019-01-04)

-   Added example script to convert a type 1 MIDI file into a type 0
    format file.
-   Moved previously private `MidiEvent` class to `miditk.smf.api`
    module and exposed it in `miditk.smf` module name space and improved
    and fixed several aspects of the `MidiEvent` class.
-   Fixed parsing of polyphonic pressure events.
-   Fixed output for polyphonic pressure events in
    `PrintingMidiEventHandler`.
-   Fix time keeping in `ObjectMidiEventHandler` for multi-track files:
    reset `current_time` attribute when new track starts.
-   Fixed: `BaseMidiEventHandler` used wrong handler method name for
    sysex messages.
-   Updated base/dev requirements.

## 0.2.1 (2018-08-20)

-   Fixed missing string formatting args in
    `PrintingMidiEventHandler.key_signature` method.
-   Added `example_program_change_map.py` script to examples.
-   Ensure support for Python 3.7.

## 0.2.0 (2018-04-18)

-   Removed Cython version of `miditk.smf.converters` module
    (`miditk.smf._speedups`). `miditk-smf` now only requires `six`.
-   Fixed `tox.ini` to work on Windows too.
-   Improved and updated readme file.

## 0.1.0 (2018-04-09)

Initial release
