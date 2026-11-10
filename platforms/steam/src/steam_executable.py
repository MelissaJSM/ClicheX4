"""Require the original build; on-disk EXE edits caused a Steam startup error."""
import hashlib

ORIGINAL_SHA256='8c549623ce4f010ee0b3c23b17fe1ea52d3bc2acfcac9be9b0ecf374cfaa6949'
JP_TITLE_OFFSET=0xb70b38


def validate_executable(raw):
    if hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA256:return 'original'
    raise ValueError('Original RXC1 executable required; file edits are not supported')
