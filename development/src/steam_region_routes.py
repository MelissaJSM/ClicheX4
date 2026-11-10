"""X4 archive-name routing for the eight modified language-shared resources.

Only the return path of X4's native archive-name lookup is adapted. All original
resource IDs, streaming lists and internal texture names are retained.
"""
import struct
SHARED=('st0_1_1','st0a_00','st0b_01','st0b_0z','st0c_00','st0d_0x','st0d_0z','stb_1_1')
# 98D490 returns the physical ARC basename. 98D4F0 returns the internal RLST
# basename and MUST remain original, even when the external filename differs.
SITES=((0x98d4b1,0xf6c914),)
CONTEXT_POINTER=0x1b43a08
ENGINE_POINTER=0x1b9b140
HQ_PRIVATE=tuple(f'cliche_{mode}_hqx_{state:02}.arc' for mode in ('rn','br') for state in range(1,18))+tuple(f'cliche_{mode}_hqz_01.arc' for mode in ('rn','br'))

def routing_data(original):
    tables=[]
    for base,count_at in [(0xf6c910,0xf6cce8),(0xf6ccf0,0xf6ccec)]:
        count=struct.unpack_from('<I',original,count_at-0x400c00)[0]
        rows=[]
        for i in range(count):
            key,ptr=struct.unpack_from('<II',original,base-0x400c00+8*i)
            start=ptr-0x400c00;end=original.find(b'\0',start)
            name=original[start:end].decode('ascii');rows.append((key,ptr,name))
        tables.append(rows)
    if tables[0]!=tables[1]:raise ValueError('Physical/internal original names differ')
    selected=[q for q in tables[0] if q[2] in SHARED]
    if set(q[2] for q in selected)!=set(SHARED) or len(selected)!=10:raise ValueError('Shared resource lookup differs')
    return tables[0],selected

def original_sites():return [(address,b'\x8b\x04\xc5'+struct.pack('<I',table)) for address,table in SITES]

def build(original,base,with_hq=False):
    _,all_routes=routing_data(original);routes=list({q[2]:q for q in all_routes}.values());blob=bytearray(4096);common=0x40;strings=0x500
    string_ptrs={}
    for _,_,name in routes:
        text=('cliche_br_'+name).encode('ascii')+b'\0';string_ptrs[name]=base+strings
        blob[strings:strings+len(text)]=text;strings+=len(text)
    if with_hq:
        for filename in HQ_PRIVATE:
            name=filename[:-4];text=name.encode('ascii')+b'\0';string_ptrs[name]=base+strings
            blob[strings:strings+len(text)]=text;strings+=len(text)
        for mode,offset in [('rn',0xd00),('br',0xd80)]:
            struct.pack_into('<17I',blob,offset,*(string_ptrs[f'cliche_{mode}_hqx_{state:02}'] for state in range(1,18)))
        if strings>=0xd00:raise ValueError('HQ string storage overflow')
    code=bytearray();fixups=[];labels={}
    def jump(op,label):code.extend(op);fixups.append((len(code),label));code.extend(bytes(4))
    # Save exactly the ECX and flags state produced by the original lookup.
    code.extend(b'\x9c\x51'+(b'\x52' if with_hq else b'')+b'\x8b\x0d'+struct.pack('<I',CONTEXT_POINTER)+b'\x85\xc9')
    jump(b'\x0f\x84','done')
    if with_hq:
        pointers={name:ptr for _,ptr,name in routes}
        code.extend(b'\x3d'+struct.pack('<I',pointers['st0d_0x']));jump(b'\x0f\x84','hqx')
        code.extend(b'\x3d'+struct.pack('<I',pointers['st0d_0z']));jump(b'\x0f\x84','hqz');jump(b'\xe9','region')
        labels['hqx']=len(code)
        code.extend(b'\x8b\x0d'+struct.pack('<I',ENGINE_POINTER)+b'\x85\xc9');jump(b'\x0f\x84','region')
        code.extend(b'\x80\xb9\xeb\x00\x00\x00\x00');jump(b'\x0f\x85','region')
        code.extend(b'\x0f\xb6\x91\xef\x00\x00\x00\x80\xb9\xdf\x00\x00\x00\x00');jump(b'\x0f\x85','ultimate')
        code.extend(b'\x83\xe2\x0f');jump(b'\xe9','x_state')
        labels['ultimate']=len(code);code.extend(b'\x85\xd2\x0f\x95\xc2\x0f\xb6\xd2\x83\xc2\x10')
        labels['x_state']=len(code);code.extend(b'\x85\xd2');jump(b'\x0f\x84','region');code.extend(b'\x4a')
        code.extend(b'\x8b\x0d'+struct.pack('<I',CONTEXT_POINTER)+b'\x83\x79\x78\x01');jump(b'\x0f\x85','x_br')
        code.extend(b'\x8b\x04\x95'+struct.pack('<I',base+0xd00));jump(b'\xe9','done')
        labels['x_br']=len(code);code.extend(b'\x8b\x04\x95'+struct.pack('<I',base+0xd80));jump(b'\xe9','done')
        labels['hqz']=len(code);code.extend(b'\x8b\x0d'+struct.pack('<I',ENGINE_POINTER)+b'\x85\xc9');jump(b'\x0f\x84','region')
        code.extend(b'\x80\xb9\xeb\x00\x00\x00\x01');jump(b'\x0f\x85','region')
        code.extend(b'\x80\xb9\xdf\x00\x00\x00\x00');jump(b'\x0f\x84','region')
        code.extend(b'\x8b\x0d'+struct.pack('<I',CONTEXT_POINTER)+b'\x83\x79\x78\x01');jump(b'\x0f\x85','z_br')
        code.extend(b'\xb8'+struct.pack('<I',string_ptrs['cliche_rn_hqz_01']));jump(b'\xe9','done')
        labels['z_br']=len(code);code.extend(b'\xb8'+struct.pack('<I',string_ptrs['cliche_br_hqz_01']));jump(b'\xe9','done')
        labels['region']=len(code);code.extend(b'\x8b\x0d'+struct.pack('<I',CONTEXT_POINTER))
    code.extend(b'\x83\x79\x78\x01');jump(b'\x0f\x84','done')
    for n,(_,ptr,name) in enumerate(routes):
        code.extend(b'\x3d'+struct.pack('<I',ptr));jump(b'\x0f\x85',f'next{n}')
        code.extend(b'\xb8'+struct.pack('<I',string_ptrs[name]));jump(b'\xe9','done');labels[f'next{n}']=len(code)
    labels['done']=len(code);code.extend((b'\x5a' if with_hq else b'')+b'\x59\x9d\xc3')
    for p,label in fixups:struct.pack_into('<i',code,p,labels[label]-(p+4))
    if common+len(code)>=0x500:raise ValueError('Routing code overlaps strings')
    blob[common:common+len(code)]=code;hooks=[]
    for i,(address,old) in enumerate(original_sites()):
        offset=i*0x20;stub=old+b'\xe9'+struct.pack('<i',common-(offset+len(old)+5));blob[offset:offset+len(stub)]=stub
        hooks.append((address,old,b'\xe9'+struct.pack('<i',base+offset-address-5)+b'\x90\x90'))
    return bytes(blob),hooks
