import hashlib
import struct
import unittest
import zlib
from src.steam_arc import SteamArc,pat_from_ps1


def fixture():
    raw=bytearray(512)
    raw[:8]=b'ARC\0'+struct.pack('<HH',7,2)
    cursor=256
    for i,payload in enumerate((b'first resource'*10,b'unchanged'*5)):
        pos=8+80*i
        name=f'X4\\test{i}'.encode('ascii')
        raw[pos:pos+len(name)]=name
        packed=zlib.compress(payload)
        struct.pack_into('<IIII',raw,pos+64,100+i,len(packed),0x40000000|len(payload),cursor)
        raw[cursor:cursor+len(packed)]=packed;cursor+=len(packed)
    return bytes(raw)


class ArcTests(unittest.TestCase):
    def test_identity_and_preserving_growth(self):
        raw=fixture();arc=SteamArc(raw,hashlib.sha256(raw).hexdigest())
        self.assertEqual(arc.rebuild({}),raw)
        changed=bytes(range(256))*20
        result=SteamArc(arc.rebuild({arc.entries[0].key:changed}))
        self.assertEqual(result.entries[0].payload,changed)
        self.assertEqual(result.entries[1].payload,arc.entries[1].payload)
        self.assertEqual(result.entries[1].flags,arc.entries[1].flags)
        self.assertEqual(result.entries[0].offset+result.entries[0].compressed_size,result.entries[1].offset)
        self.assertEqual(result.entries[0].flags,0x40000000)

    def test_wrong_source_and_unknown_key(self):
        with self.assertRaises(ValueError):SteamArc(fixture(),'0'*64)
        with self.assertRaises(ValueError):SteamArc(fixture()).rebuild({('missing',0):b'x'})

    def test_overlap_and_length_corruption(self):
        raw=bytearray(fixture())
        struct.pack_into('<I',raw,8+80+76,256)
        with self.assertRaises((ValueError,zlib.error)):SteamArc(raw)
        raw=bytearray(fixture())
        struct.pack_into('<I',raw,8+72,0x40000001)
        with self.assertRaises(ValueError):SteamArc(raw)

    def test_shared_ps1_parts_are_expanded_without_changing_coordinates(self):
        quad=bytes((0x40,3,0xf8,0xe0))
        parts=struct.pack('<IHHHH',4,1,2,1,2)+quad
        pat=pat_from_ps1(parts)
        self.assertEqual(pat[:24],b'PAT\0'+struct.pack('<IIIII',3,1,2,1,1))
        self.assertEqual(pat[24:32],struct.pack('<HHHH',1,2,1,3))
        self.assertEqual(pat[32:],quad*2)

    def test_streaming_loader_order_is_checked_even_when_payloads_decode(self):
        raw=bytearray(fixture())
        first=bytes(raw[8:88]);second=bytes(raw[88:168])
        raw[8:88]=second;raw[88:168]=first
        arc=SteamArc(raw)
        self.assertEqual(arc.entries[0].payload,b'unchanged'*5)
        with self.assertRaises(ValueError):arc.validate_stream_order()


if __name__=='__main__':unittest.main()
