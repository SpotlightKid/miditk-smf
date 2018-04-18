# -*- coding: utf-8 -*-
#
# miditk/smf/converters.py
#
"""Functions for reading and writing the special data types in a MIDI file."""

__all__ = (
    'read_bew',
    'read_varlen',
    'sizeof_varlen',
    'tointseq',
    'tobytestr',
    'write_bew',
    'write_varlen'
)

# _speedups module not available
from struct import pack, unpack

from six import iterbytes, text_type


if isinstance(b'', str):
    def _tobytes(*values):
        return "".join(chr(c) for c in values)
else:
    def _tobytes(*values):
        return bytes(values)


def _ord(x):
    return x if isinstance(x, int) else ord(x)


def read_bew(value):
    """Read byte string as big endian word.

    Variable Length Data (varlen) is a data format sprayed liberally throughout a midi file. It can
    be anywhere from 1 to 4 bytes long. If the 8'th bit is set in a byte another byte follows. The
    value is stored in the lowest 7 bits of each byte. So maximum value is 2^28 (4x7 bits = 28
    bits) = 268435456.

    ::

        >>> read_bew(b'aáâã')
        1642193635
        >>> read_bew(b'aá')
        25057

    """
    lval = len(value)
    if lval == 1:
        return _ord(value)
    elif lval == 2:
        return unpack('>H', value)[0]
    else:
        return unpack('>L', value)[0]


def read_varlen(value):
    """Convert variable length data format to integer.

    Just pass it 0 or more chars that might be a varlen and it will only use
    the relevant chars.

    Use sizeof_varlen(value) to see how many bytes the integer value takes.

    ::

        >>> read_varlen(b'@')
        64
        >>> read_varlen(b'áâãa')
        205042145

    """
    sum = 0
    for byte in iterbytes(value):
        sum = (sum << 7) + (byte & 0x7F)

        if not 0x80 & byte:
            # stop after last byte with high bit set
            break

    return sum


def sizeof_varlen(value):
    """Return number of bytes an integer will need when converted to varlength."""
    if value <= 127:
        return 1
    elif value <= 16383:
        return 2
    elif value <= 2097151:
        return 3
    else:
        return 4


def tobytestr(value, encoding='latin1'):
    """Convert given string or sequence of integers to a byte string."""
    if isinstance(value, text_type):
        value = value.encode(encoding)
    elif isinstance(value, (list, tuple)):
        value = _tobytes(*value)
    return value


def tointseq(value, encoding='latin1'):
    """Convert a bytes/str/unicode instance into a tuple of int byte values."""
    if isinstance(value, text_type):
        value = value.encode(encoding)
    return tuple(_ord(c) for c in value)


def write_bew(value, length):
    """Write int as big endian formatted bytes string.

    >>> read_bew(write_bew(25057, 2))
    25057
    >>> long(read_bew(write_bew(1642193635L, 4)))
    1642193635L

    """
    if length == 1:
        return _tobytes(value)
    elif length == 2:
        return pack('>H', value)
    else:
        return pack('>L', value)


def write_varlen(value):
    """Convert an integer to varlength format."""
    nbytes = sizeof_varlen(value)
    if nbytes == 1:
        return _tobytes(value)
    else:
        return b"".join(_tobytes(((value >> ((i - 1) * 7)) | 0x80) & (0xFF if i > 1 else 0x7F))
                        for i in range(nbytes, 0, -1))
