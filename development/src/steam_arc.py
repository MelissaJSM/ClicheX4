"""Bounded reader and preserving writer for the verified MT ARC v7 variant."""
from dataclasses import dataclass
import hashlib
import struct
import zlib


@dataclass(frozen=True)
class ArcEntry:
    index: int
    name: str
    kind: int
    flags: int
    offset: int
    compressed_size: int
    payload: bytes

    @property
    def key(self):
        return self.name, self.kind


class SteamArc:
    def __init__(self, raw, expected_sha256=None):
        self.raw = bytes(raw)
        if expected_sha256 is not None and hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise ValueError('Unsupported ARC hash')
        if len(raw)<8 or raw[:4]!=b'ARC\0':raise ValueError('Invalid ARC header')
        version,count=struct.unpack_from('<HH',raw,4)
        if version!=7 or len(raw)<8+80*count:raise ValueError('Unsupported ARC version/directory')
        self.entries=[]
        keys=set();ranges=[]
        for i in range(count):
            pos=8+80*i
            name=raw[pos:pos+64].split(b'\0')[0].decode('ascii')
            kind,compressed,size_flags,offset=struct.unpack_from('<IIII',raw,pos+64)
            size=size_flags&0x1fffffff
            if offset<8+80*count or offset+compressed>len(raw) or size>64*1024*1024:
                raise ValueError('ARC entry outside limits')
            dec=zlib.decompressobj()
            payload=dec.decompress(raw[offset:offset+compressed],size+1)
            if len(payload)!=size or not dec.eof or dec.unused_data or dec.unconsumed_tail:
                raise ValueError('ARC invalid compressed length')
            item=ArcEntry(i,name,kind,size_flags&0xe0000000,offset,compressed,payload)
            if item.key in keys:raise ValueError('Duplicate ARC key')
            keys.add(item.key);ranges.append((offset,offset+compressed));self.entries.append(item)
        ranges.sort()
        if any(a[1]>b[0] for a,b in zip(ranges,ranges[1:])):raise ValueError('ARC overlapping entries')
        self.by_key={e.key:e for e in self.entries}

    def validate_stream_order(self):
        if any(a.offset+a.compressed_size!=b.offset for a,b in zip(self.entries,self.entries[1:])):
            raise ValueError('RXC1 streaming loader requires contiguous directory-order payloads')

    def rebuild(self, updates):
        if not set(updates)<=set(self.by_key):raise ValueError('Unknown replacement key')
        if all(bytes(v)==self.by_key[k].payload for k,v in updates.items()):return self.raw
        first=self.entries[0].offset
        self.validate_stream_order()
        end=self.entries[-1].offset+self.entries[-1].compressed_size
        result=bytearray(self.raw[:first])
        for old in self.entries:
            payload=bytes(updates.get(old.key,old.payload))
            if len(payload)>64*1024*1024:raise ValueError('Replacement exceeds verified limit')
            compressed=(zlib.compress(payload,9) if payload!=old.payload else
                        self.raw[old.offset:old.offset+old.compressed_size])
            offset=len(result)
            result.extend(compressed)
            struct.pack_into('<III',result,8+80*old.index+68,len(compressed),old.flags|len(payload),offset)
        result.extend(self.raw[end:])
        verified=SteamArc(result)
        for item in verified.entries:
            old=self.by_key[item.key]
            if item.payload!=updates.get(item.key,old.payload) or item.flags!=old.flags:
                raise ValueError('ARC read-back mismatch')
        return bytes(result)


def pat_from_ps1(parts):
    """Reorder existing packed frame headers/quad banks into the matched PAT v3."""
    first=struct.unpack_from('<I',parts)[0]
    if first%4 or not 4<=first<=len(parts):raise ValueError('PS1 parts directory')
    starts=list(struct.unpack_from('<'+'I'*(first//4),parts))
    if starts!=sorted(set(starts)):raise ValueError('PS1 parts bank ordering')
    prefix=bytearray(b'PAT\0'+struct.pack('<II',3,len(starts)))
    headers,quads=[],[]
    for i,start in enumerate(starts):
        end=starts[i+1] if i+1<len(starts) else len(parts)
        if not first<=start<end<=len(parts):raise ValueError('PS1 bank bounds')
        n=struct.unpack_from('<H',parts,start+2)[0]
        if not 0<n<=4096 or start+n*4>end:raise ValueError('PS1 frame bounds')
        counts=[];offset=n;bank_headers=bytearray();bank_quads=bytearray()
        for j in range(n):
            count,loc=struct.unpack_from('<HH',parts,start+j*4)
            if loc<n or start+(loc+count)*4>end:raise ValueError('Quad reference out of bank bounds')
            if offset>65535:raise ValueError('PAT quad address limit exceeded')
            bank_headers.extend(struct.pack('<HH',count,offset))
            bank_quads.extend(parts[start+loc*4:start+(loc+count)*4])
            counts.append(count);offset+=count
        prefix.extend(struct.pack('<I',n)+struct.pack('<'+'I'*n,*counts))
        headers.append(bytes(bank_headers));quads.append(bytes(bank_quads))
    return bytes(prefix)+b''.join(headers)+b''.join(quads)
