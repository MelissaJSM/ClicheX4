import hashlib
import struct
import unittest

from scripts.build_riko_voice import replace_voice_body
from scripts.discover_inputs import psx_arc


class VoicePatchTests(unittest.TestCase):
    def fixture(self):
        arc = bytearray(6144)
        struct.pack_into('<II', arc, 0, 14, len(arc))
        struct.pack_into('<II', arc, 8+12*8, 6, 32)
        struct.pack_into('<II', arc, 8+13*8, 0x20301, 64)
        body = bytearray(64)
        body[17], body[33], body[49] = 4, 1, 7
        arc[4096:4160] = body
        arc = bytes(arc)
        entries = psx_arc(arc)
        source = {'parent_arc_sha256': hashlib.sha256(arc).hexdigest(),
                  'voice_body_entry': entries[13], 'voice_header_entry': entries[12],
                  'commands': [{'body_offset':0, 'bytes':64}]}
        body[18] = 1
        return arc, bytes(body), source

    def test_only_sample_bytes_change(self):
        arc, body, source = self.fixture()
        result = replace_voice_body(arc, body, source)
        self.assertEqual(len(result), len(arc))
        self.assertEqual([i for i,(a,b) in enumerate(zip(arc,result)) if a != b], [4114])

    def test_rejects_wrong_parent_length_flags_reserved_and_overlap(self):
        arc, body, source = self.fixture()
        cases = [(arc+b'x',body,source), (arc,body[:-1],source),
                 (arc,body[:17]+bytes([3])+body[18:],source),
                 (arc,body[:-1]+b'x',source),
                 (arc,body,{**source,'commands':source['commands']*2}),
                 (arc,body,{**source,'commands':[]})]
        for a,b,s in cases:
            with self.assertRaises(ValueError): replace_voice_body(a,b,s)


if __name__ == '__main__': unittest.main()
