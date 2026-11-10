"""Select only X's drawn armor layers; never change owned equipment or abilities."""
import struct

SITES=(0xaa85b8,0xaa85cf,0xaa85e6,0xaa860d)
GETTER=0x98eca0
ENGINE=0x1b9b140

def call(site,target):return b'\xe8'+struct.pack('<i',target-site-5)
def original_sites():return [(a,call(a,GETTER)) for a in SITES]

def build(base):
    code=bytearray(call(base,GETTER));labels={};fix=[]
    def emit(b):code.extend(b)
    def branch(op,label):emit(op);fix.append((len(code),label));emit(bytes(4))
    # Native getter adds 0xbc to ECX, sets only AL and modifies flags.
    # Preserve those results except AL, which is local to this draw routine.
    emit(b'\x9c\x51\x52\x8b\x15'+struct.pack('<I',ENGINE)+b'\x85\xd2')
    branch(b'\x0f\x84','done')
    emit(b'\x80\xba\xeb\x00\x00\x00\x00');branch(b'\x0f\x85','done')
    emit(b'\x80\xba\xdf\x00\x00\x00\x00');branch(b'\x0f\x84','done')
    emit(b'\x80\xba\xef\x00\x00\x00\x00');branch(b'\x0f\x84','layers')
    # The native renderer gets its displayed actor from [ESI+0x38].
    # 98e070 -> a9b480 proves the current frame is actor+0x66.
    emit(b'\x8b\x4e\x38\x85\xc9');branch(b'\x0f\x84','done')
    emit(b'\x0f\xb6\x51\x66\x81\xea\xd9\x00\x00\x00\x83\xfa\x0e')
    branch(b'\x0f\x82','layers')
    emit(b'\xb0\x00');branch(b'\xe9','done')
    labels['layers']=len(code);emit(b'\xb0\x0f')
    labels['done']=len(code);emit(b'\x5a\x59\x9d\xc3')
    for at,label in fix:struct.pack_into('<i',code,at,labels[label]-at-4)
    if len(code)>4096:raise ValueError('Ultimate draw adapter overflow')
    blob=bytes(code)+bytes(4096-len(code))
    return blob,[(a,old,call(a,base)) for a,old in original_sites()]

# Signatures establish the native actor, frame, armor and arm-type offsets.
SIGNATURES={
    0x97f080:'a140b1b901c3',0x97f0a0:'8d8134080000c3',
    0x98eca0:'81c1bc000000e985d11000',0xa9be30:'8a81d4000000c3',
    0x98e070:'83c124e908d41000',0xa9b480:'8a4142c3',
    0x98ea50:'81c1bc000000e9f5d11000',0xa9bc50:'8a81e5000000c3',
}
