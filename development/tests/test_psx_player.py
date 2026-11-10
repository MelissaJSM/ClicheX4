import struct
import unittest

from src.psx_player import decode_stream, indexed_atlas, composition_frame, compose_indices


def words(*values):
    return struct.pack('<'+'H'*len(values), *values)


class PlayerCodecTests(unittest.TestCase):
    def test_literals_overlap_zero_run_and_exact_serialization(self):
        # 2 literals, overlapping distance 2 copy, short zero run, long zero run, end.
        data = words(0x3fff, 0x1234, 0x5678, (4 << 11)|2, 2 << 11, 0, 32, 0, 0)
        stream = decode_stream(data, 0, len(data), 80)
        self.assertEqual(stream.data, words(0x1234,0x5678,0x1234,0x5678,0x1234,0x5678)+bytes(68))
        self.assertEqual(stream.serialize(), data)
        self.assertEqual(stream.owners[:6], [2,4,2,4,2,4])

    def test_long_back_reference(self):
        data = words(0x7fff, 0xabcd, 1, 40, 0, 0)
        stream = decode_stream(data, 0, len(data), 82)
        self.assertEqual(stream.data, words(*([0xabcd]*41)))
        self.assertEqual(stream.serialize(), data)

    def test_truncation_invalid_reference_and_budget_rejected(self):
        for data, size in [(words(0),2), (words(0xffff,0x0801),2),
                           (words(0xffff,0x1000),2), (words(0xffff,0,0),2),
                           (words(0xffff,1,0),2)]:
            with self.subTest(data=data), self.assertRaises(ValueError):
                decode_stream(data,0,len(data),size)

    def test_nibble_order_and_partial_upload_row(self):
        packed = bytes([0x21])*17*128
        atlas, locations, height = indexed_atlas(packed,17)
        self.assertEqual(height,32)
        self.assertEqual(atlas[:2],b'\x01\x02')
        self.assertEqual(locations[16*256],(2048,0))
        self.assertIsNone(locations[16*256+16])

    def test_parts_flip_signed_origin_and_bad_tile(self):
        # One bank, one frame, one horizontally flipped tile at (-4,-8).
        data = words(4,0,1,1)+struct.pack('<BBbb',0x40,0,-4,-8)
        frame=composition_frame(data,0,0)
        indices,size,bounds,_=compose_indices(bytes([0x21])*128,1,frame)
        self.assertEqual(size,(16,16)); self.assertEqual(bounds,(-4,-8,12,8))
        self.assertEqual(indices[:2],b'\x02\x01')
        frame['parts'][0]['tile']=1
        with self.assertRaises(ValueError): compose_indices(bytes(128),1,frame)


if __name__ == '__main__':
    unittest.main()
