import struct
import unittest

from src.psx_bank_repack import repack_graphics_bank
from src.psx_compress import encode_stream
from src.psx_player import graphics_bank, decode_stream


def fixture(slack=200, aliases=False):
    codes = [encode_stream(bytes(128)), encode_stream(bytes([17])*128)]
    count = 3 if aliases else 2
    starts = [count*4, count*4+len(codes[0])+12]
    size = starts[1]+len(codes[1])+slack
    size = (size+3)//4*4
    source = bytearray(struct.pack('<II', 8, 8+size)+bytes(size)+b'TAIL')
    for i, start in enumerate(starts + ([starts[1]] if aliases else [])):
        struct.pack_into('<I', source, 8+i*4, 1 << 20 | start)
    for start, code in zip(starts, codes):
        source[8+start:8+start+len(code)] = code
    return source


class BankRepackTests(unittest.TestCase):
    def test_expansion_preserves_unselected_stream_and_other_bank(self):
        source = fixture(); before = bytes(source)
        old = graphics_bank(source, 0)
        replacement = encode_stream(struct.pack('<64H', *range(64)))
        result, report = repack_graphics_bank(source, 0, {0: replacement})
        new = graphics_bank(result, 0)
        self.assertEqual(bytes(source), before)
        self.assertEqual(len(result), len(source))
        self.assertEqual(result[:8], source[:8])
        self.assertEqual(result[old['end']:], b'TAIL')
        self.assertEqual(new['frames'][0]['offset'], 16)
        self.assertEqual(new['end'], old['end'])
        f0 = old['frames'][1]; f1 = new['frames'][1]
        decoded = decode_stream(source, f0['offset'], f0['limit'], 128)
        self.assertEqual(result[f1['offset']:f1['offset']+decoded.end-f0['offset']], source[f0['offset']:decoded.end])
        self.assertGreater(f1['offset'], f0['offset'])
        self.assertGreaterEqual(report['remaining_slack'], 0)
        self.assertEqual(repack_graphics_bank(source, 0, {0: replacement}), (result, report))

    def test_partial_and_conflicting_aliases_rejected(self):
        source = fixture(aliases=True)
        a, b = encode_stream(bytes(128)), encode_stream(bytes([3])*128)
        for replacements in ({1:a}, {1:a, 2:b}):
            with self.assertRaises(ValueError):repack_graphics_bank(source, 0, replacements)
        result, _ = repack_graphics_bank(source, 0, {1:a, 2:a})
        frames = graphics_bank(result, 0)['frames']
        self.assertEqual(frames[1]['offset'], frames[2]['offset'])

    def test_capacity_and_invalid_replacement_rejected_without_mutation(self):
        source = fixture(slack=0); before = bytes(source)
        huge = encode_stream(struct.pack('<64H', *range(64)))
        for replacements in ({}, {3:huge}, {0:huge}, {0:b'\x00'},
                             {0:encode_stream(bytes(256))}, {0:encode_stream(bytes(128))+b'xx'}):
            with self.assertRaises(ValueError):repack_graphics_bank(source, 0, replacements)
        self.assertEqual(bytes(source), before)

    def test_bank_alias_and_conflicting_tile_counts_rejected(self):
        source = fixture(aliases=True)
        frame = struct.unpack_from('<I', source, 16)[0]
        struct.pack_into('<I', source, 16, 2 << 20 | (frame & 0xfffff))
        with self.assertRaises(ValueError):repack_graphics_bank(source, 0, {0:encode_stream(bytes(128))})
        source = fixture(); struct.pack_into('<I', source, 4, 8)
        with self.assertRaises(ValueError):repack_graphics_bank(source, 0, {0:encode_stream(bytes(128))})


if __name__ == '__main__':
    unittest.main()
