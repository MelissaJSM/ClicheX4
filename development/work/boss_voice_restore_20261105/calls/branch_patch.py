"""Apply the one guarded boss-intro call branch to EXE bytes, without disk writes."""
import hashlib
SOURCE_EXE_SHA256='1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab'
ADDRESS=0x800921f8
OFFSET=ADDRESS-0x8000f800
BEFORE=bytes.fromhex('18004014')
AFTER=bytes(4)
def patch_executable(exe):
    if hashlib.sha256(exe).hexdigest()!=SOURCE_EXE_SHA256:
        raise ValueError('Current supported EXE hash mismatch')
    if exe[OFFSET:OFFSET+4]!=BEFORE:
        raise ValueError('Boss intro branch mismatch')
    out=bytearray(exe);out[OFFSET:OFFSET+4]=AFTER
    assert exe[:OFFSET]==out[:OFFSET] and exe[OFFSET+4:]==out[OFFSET+4:]
    return bytes(out)
