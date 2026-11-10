"""Display-only pause/save outfit selection for the verified native X4 build."""
import struct

ENGINE = 0x1b9b140
PAUSE = 0x983fa4
FRAME = 0xa9ff35
PALETTE = 0xa9ff5f
OVERLAY = 0xa9fcb3

def rel(op, site, target):
    return op + struct.pack('<i', target-site-len(op)-4)

def original_sites():
    return [(PAUSE, bytes.fromhex('8a1cf5f4d8f500')),
            (FRAME, rel(b'\xe8', FRAME, 0x98e190)),
            (PALETTE, rel(b'\xe8', PALETTE, 0x98e150)),
            (OVERLAY, rel(b'\x0f\x85', OVERLAY, 0xa9fdc8))]

SIGNATURES = {
    0x97f080: 'a140b1b901c3',
    0x98e190: '83c124e978d31000',
    0xa9b510: '8a442404884142c20400',
    0x98e150: '83c124e998d31000',
    0xa9b4f0: '668b4424046689413ac20400',
    0xa9ff2c: '803f008bce7517',
    0xa9fca3: '807d00000f850e020000807d29005356',
}

def build(base):
    code=bytearray(); hooks=[]
    def routine():
        start=len(code); labels={}; fixes=[]
        def emit(b):code.extend(b)
        def branch(op,label):
            emit(op);fixes.append((len(code),label));emit(bytes(4))
        def label(n):labels[n]=len(code)
        def finish():
            for at,n in fixes:struct.pack_into('<i',code,at,labels[n]-at-4)
        return start,emit,branch,label,finish
    start,emit,branch,label,finish=routine()
    emit(original_sites()[0][1])
    emit(b'\x9c\x50\x52\x83\xfe\x1e');branch(b'\x0f\x85','done')
    emit(b'\x8b\x15'+struct.pack('<I',ENGINE)+b'\x85\xd2');branch(b'\x0f\x84','done')
    emit(b'\x80\xba\xeb\x00\x00\x00\x00');branch(b'\x0f\x85','zero')
    emit(b'\x0f\xb6\x82\xef\x00\x00\x00')
    emit(b'\x80\xba\xdf\x00\x00\x00\x00');branch(b'\x0f\x85','ultimate')
    emit(b'\x83\xe0\x03');branch(b'\xe9','pick')
    label('ultimate');emit(b'\x85\xc0\x0f\x95\xc0\x0f\xb6\xc0\x83\xc0\x04');branch(b'\xe9','pick')
    label('zero');emit(b'\x80\xba\xdf\x00\x00\x00\x00\x0f\x95\xc0\x0f\xb6\xc0')
    label('pick');emit(b'\x04\x26\x88\xc3')
    label('done');emit(b'\x5a\x58\x9d');emit(rel(b'\xe9',base+len(code),PAUSE+7));finish()
    hooks.append((PAUSE,original_sites()[0][1],rel(b'\xe9',PAUSE,base+start)+b'\x90\x90'))
    for site,target,first in [(FRAME,0x98e190,52),(PALETTE,0x98e150,30)]:
        start,emit,branch,label,finish=routine()
        # EDI is the slot selected by 996bd0, not the current player.
        # Keep original setter contract; only replace its stack argument.
        emit(b'\x9c\x50\x80\x3f\x00');branch(b'\x0f\x85','done')
        emit(b'\x80\x7f\x29\x00');branch(b'\x0f\x84','done')
        emit(b'\x0f\xb6\x47\x03\x83\xe0\x0f\x0f\x95\xc0\x0f\xb6\xc0')
        emit(b'\x83\xc0'+bytes([first])+b'\x89\x44\x24\x0c')
        label('done');emit(b'\x58\x9d');emit(rel(b'\xe9',base+len(code),target));finish()
        hooks.append((site,rel(b'\xe8',site,target),rel(b'\xe8',site,base+start)))
    # Special X uses one complete frame. Skip only its old extra armor object.
    hooks.append((OVERLAY,original_sites()[-1][1],rel(b'\x0f\x85',OVERLAY,0xa9feb9)))
    if len(code)>4096:raise ValueError('Menu adapter overflow')
    return bytes(code)+bytes(4096-len(code)),hooks
