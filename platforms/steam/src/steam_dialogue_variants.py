"""Display-only Ultimate animation-table and Black Zero palette adapters."""
import struct
ANIMATION_SITE=0x981f96
PALETTE_SITE=0x98200b
def call_bytes(site,target):return b'\xe8'+struct.pack('<i',target-site-5)
def original_sites():return [(ANIMATION_SITE,call_bytes(ANIMATION_SITE,0x98e210)),(PALETTE_SITE,call_bytes(PALETTE_SITE,0x98e150))]
def native_sequences():
    return b''.join(bytes([1,1,0,n,7,0,1,n,6,0,1,n+4,1,1,0,n+4]) for n in range(4))

def build(base,palettes):
    blob=bytearray(4096)
    for mode,offset in [('rn',0xc00),('br',0xc40)]:
        for variant,shift in [('normal_hex',0),('black_hex',32)]:
            data=bytes.fromhex(palettes[mode][variant])
            if len(data)!=32:raise ValueError('Zero palette length')
            blob[offset+shift:offset+shift+32]=data
    for post,offset in [(False,0x800),(True,0xa00)]:
        loc=offset+32;ptrs=[]
        for n in range(4):
            for record in [bytes([1,1,0,n]),bytes([7,0,1,n,6,0,1,n+4,1,1,0,n+4])]:
                data=bytearray(record)
                for p in range(3,len(data),4):data[p]=(9 if post else 8)+(2 if data[p]>=4 else 0)
                ptrs.append(base+loc);blob[loc:loc+len(data)]=data;loc+=len(data)
        struct.pack_into('<8I',blob,offset,*ptrs)
    def assemble(offset,body,tail):
        code=bytearray();fix=[];labels={}
        def emit(data):code.extend(data)
        def jump(op,label):emit(op);fix.append((len(code),label));emit(bytes(4))
        def label(name):labels[name]=len(code)
        body(emit,jump,label)
        emit(b'\xe9'+struct.pack('<i',tail-(base+offset+len(code)+5)))
        for p,l in fix:struct.pack_into('<i',code,p,labels[l]-(p+4))
        if len(code)>0x400:raise ValueError('Display adapter exceeds allocation')
        blob[offset:offset+len(code)]=code
    def animation(e,j,l):
        e(b'\x9c\x50\x52\x81\x7c\x24\x10'+struct.pack('<I',0x1adb108));j(b'\x0f\x85','done')
        e(b'\xa1'+struct.pack('<I',0x1b9b140)+b'\x85\xc0');j(b'\x0f\x84','done')
        e(b'\x80\xb8\xeb\x00\x00\x00\x00');j(b'\x0f\x85','done')
        e(b'\x80\xb8\xdf\x00\x00\x00\x00');j(b'\x0f\x84','done')
        e(b'\xba'+struct.pack('<I',base+0x800)+b'\x80\xb8\xef\x00\x00\x00\x00');j(b'\x0f\x84','set')
        e(b'\xba'+struct.pack('<I',base+0xa00));l('set');e(b'\x89\x54\x24\x10');l('done');e(b'\x5a\x58\x9d')
    def palette(e,j,l):
        e(b'\x9c\x60\xa1'+struct.pack('<I',0x1b9b140)+b'\x85\xc0');j(b'\x0f\x84','done')
        e(b'\x80\xb8\xeb\x00\x00\x00\x01');j(b'\x0f\x85','done')
        e(b'\x8b\x0d'+struct.pack('<I',0x1b43a08)+b'\x85\xc9');j(b'\x0f\x84','done')
        e(b'\xbe'+struct.pack('<I',base+0xc00)+b'\x83\x79\x78\x01');j(b'\x0f\x84','color')
        e(b'\xbe'+struct.pack('<I',base+0xc40));l('color')
        e(b'\x80\xb8\xdf\x00\x00\x00\x00');j(b'\x0f\x84','destination');e(b'\x83\xc6\x20')
        l('destination');e(b'\x8b\x15'+struct.pack('<I',0x1b9b11c)+b'\x85\xd2');j(b'\x0f\x84','done')
        e(b'\x8b\x44\x24\x28\x3d\x80\x00\x00\x00');j(b'\x0f\x83','done')
        e(b'\xc1\xe0\x05\x8d\xbc\x02\x2c\x00\x01\x00\xb9\x08\x00\x00\x00\xfc\xf3\xa5\x80\x8a\x2c\x80\x02\x00\x01')
        l('done');e(b'\x61\x9d')
    assemble(0,animation,0x98e210);assemble(0x400,palette,0x98e150)
    return bytes(blob),[(site,old,call_bytes(site,base+off)) for (site,old),off in zip(original_sites(),[0,0x400])]
