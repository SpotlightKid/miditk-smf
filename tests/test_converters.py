# -*- coding: UTF-8 -*-

import pytest

from miditk.smf.converters import read_bew, read_varlen, tobytestr, write_bew, write_varlen


def test_read_bew():
    """Test that 'read_bew' returns correct values."""
    assert read_bew(b'a\xe1\xe2\xe3') == 1642193635
    assert read_bew(b'\x04\x00') == 1024
    assert read_bew(b'\x7f') == 127


def test_read_varlen():
    """Test that 'read_varlen' returns correct values."""
    assert read_varlen(b'\xc0\x00') == 8192
    assert read_varlen(b'\xe1\xe3\xe2a') == 205058401


def test_write_bew():
    """Test that 'read_bew' returns correct values."""
    assert write_bew(1642193635, 4) == b'a\xe1\xe2\xe3'
    assert write_bew(1024, 2) == b'\x04\x00'
    assert write_bew(127, 1) == b'\x7f'


@pytest.mark.parametrize("test_input,expected", [
    (192, b'\x81\x40'),
    (8192, b'\xc0\x00'),
    (0x00000000, b'\0'),
    (0x00000040, b'\x40'),
    (0x0000007F, b'\x7F'),
    (0x00000080, b'\x81\x00'),
    (0x00002000, b'\xC0\x00'),
    (0x00003FFF, b'\xFF\x7F'),
    (0x00004000, b'\x81\x80\x00'),
    (0x00100000, b'\xC0\x80\x00'),
    (0x001FFFFF, b'\xFF\xFF\x7F'),
    (0x00200000, b'\x81\x80\x80\x00'),
    (0x08000000, b'\xC0\x80\x80\x00'),
    (0x0FFFFFFF, b'\xFF\xFF\xFF\x7F'),
])
def test_write_varlen(test_input, expected):
    """Test that 'write_varlen' returns correct values."""
    assert write_varlen(test_input) == expected


def test_tobytestr():
    assert tobytestr((48, 49, 50)) == b'\x30\x31\x32'
    assert tobytestr('\x30\x31\x32') == b'\x30\x31\x32'
    assert tobytestr(u'\x30\x31\x32') == b'\x30\x31\x32'
    assert tobytestr(b'\x30\x31\x32') == b'\x30\x31\x32'


def tointseq():
    assert tointseq('\x30\x31\x32') == (48, 49, 50)
    assert tointseq(u'\x30\x31\x32') == (48, 49, 50)
    assert tointseq(b'\x30\x31\x32') == (48, 49, 50)
