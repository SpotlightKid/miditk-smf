Changelog
#########

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
