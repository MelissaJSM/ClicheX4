"""Fixed-length English glyph-name edits, preserving PS1 dialogue flags."""
import struct

ALPHABET='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
def codes(text):return tuple(ALPHABET.index(c)+64 for c in text)

def message_ranges(data):
    if len(data)<4 or len(data)%2:raise ValueError('Invalid dialogue length')
    first=struct.unpack_from('<H',data)[0]
    if first<2 or first%2 or first>=len(data):raise ValueError('Invalid dialogue directory')
    offsets=struct.unpack_from('<'+'H'*(first//2),data)
    if list(offsets)!=sorted(offsets) or any(x<first or x%2 or x>=len(data) for x in offsets):raise ValueError('Invalid message offset')
    return [(a,b) for a,b in zip(offsets,(*offsets[1:],len(data)))]

def rename_zero(data):
    out=bytearray(data);changes=[]
    for message,(start,end) in enumerate(message_ranges(data)):
        words=struct.unpack('<'+'H'*((end-start)//2),data[start:end]);glyphs=[v&511 for v in words]
        for old,new in [('Zero','Riko'),('ZERO','RIKO')]:
            source=codes(old);target=codes(new)
            for j in range(len(words)-3):
                if tuple(glyphs[j:j+4])!=source:continue
                offset=start+j*2
                for k,value in enumerate(target):struct.pack_into('<H',out,offset+2*k,(words[j+k]&~511)|value)
                changes.append({'message':message,'offset':offset,'from':old,'to':new})
    # Directory, control flags, and all bytes outside the identified names stay exact.
    allowed={r['offset']+k for r in changes for k in range(8)}
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(data,out))):raise AssertionError('Text edit escaped name')
    for i in range(0,len(data),2):
        if struct.unpack_from('<H',data,i)[0]&~511!=struct.unpack_from('<H',out,i)[0]&~511:raise AssertionError('Text control changed')
    return bytes(out),changes
