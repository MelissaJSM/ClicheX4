"""Verified X4 death-orb palette operand; no EXE-file or motion changes."""
import hashlib

TEXT_BASE = 0x401000
TEXT_SHA256 = '38ff6b3ca58e7f4119b8ff5082bd0ad68429134eb90ffd3074da77341148e6cc'
START, SIZE = 0xA78590, 0x23B
ADDRESS = 0xA7860F
BEFORE, AFTER = b'\x02', b'\x00'


def signatures(text):
    if hashlib.sha256(text).hexdigest() != TEXT_SHA256:
        raise ValueError('Unsupported original native code')
    original = text[START - TEXT_BASE:START - TEXT_BASE + SIZE]
    if original[ADDRESS - START - 1:ADDRESS - START + 1] != b'\x6a\x02':
        raise ValueError('Death palette operand changed')
    patched = bytearray(original)
    patched[ADDRESS - START] = 0
    return original, bytes(patched)
