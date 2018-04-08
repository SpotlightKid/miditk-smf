# -*- coding: utf-8 -*-
#
# miditk/smf/_speedups.pyx
#
"""Cython version of the functions from the converters module for speed-ups."""

__all__ = (
    'read_bew',
    'read_varlen',
    'sizeof_varlen',
    'tointseq',
    'tobytestr'
    'write_bew',
    'write_varlen'
)


from libc.stdint cimport *

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
    cdef int lval = len(value)

    if lval == 1:
        return _ord(value)
    elif lval == 2:
        return unpack('>H', value)[0]
    else:
        return unpack('>L', value)[0]


def read_varlen(value):
    cdef int sum = 0
    cdef unsigned char byte

    for byte in iterbytes(value):
        sum = (sum << 7) + (byte & 0x7F)

        if not 0x80 & byte:
            break

    return sum


def sizeof_varlen(int value):
    if value <= 127:
        return 1
    elif value <= 16383:
        return 2
    elif value <= 2097151:
        return 3
    else:
        return 4


def tobytestr(value, encoding='latin1'):
    if isinstance(value, text_type):
        value = value.encode(encoding)
    elif isinstance(value, (list, tuple)):
        value = _tobytes(*value)
    return value


def tointseq(value, encoding='latin1'):
    if isinstance(value, text_type):
        value = value.encode(encoding)
    return tuple(_ord(c) for c in value)


def write_bew(int value, int length):
    if length == 1:
        return _tobytes(value)
    elif length == 2:
        return pack('>H', value)
    else:
        return pack('>L', value)


def write_varlen(int value):
    cdef int nbytes = sizeof_varlen(value)
    cdef int i
    if nbytes == 1:
        return _tobytes(value)
    else:
        return b"".join(_tobytes(((value >> ((i - 1) * 7)) | 0x80) & (0xFF if i > 1 else 0x7F))
                        for i in range(nbytes, 0, -1))
