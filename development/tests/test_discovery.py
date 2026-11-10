"""가짜 바이트만 사용하는 읽기 파서의 경계 검사. 게임 자산 불필요."""
import io
import struct
import unittest
import zlib

from scripts.discover_inputs import DiscReader, mt_arc, psx_arc


class DiscoveryTests(unittest.TestCase):
    def test_disc_rejects_wrong_sector_size(self):
        with self.assertRaises(ValueError):
            DiscReader(io.BytesIO(b''), 2048)

    def test_form2_cannot_be_read_as_form1(self):
        data = bytearray(2352)
        data[:12] = b'\0'+b'\xff'*10+b'\0'
        data[15] = 2
        data[18] = data[22] = 0x20
        reader = DiscReader(io.BytesIO(data), len(data))
        with self.assertRaises(ValueError):
            reader.sector(0)

    def test_iso_rejects_disagreeing_endian_values(self):
        record = bytearray(34)
        record[0] = 34
        struct.pack_into('<I', record, 2, 19)
        struct.pack_into('>I', record, 6, 20)
        with self.assertRaises(ValueError):
            DiscReader.record(record)

    def test_psx_arc_rejects_out_of_bounds_entry(self):
        data = bytearray(4096)
        struct.pack_into('<IIII', data, 0, 1, 4096, 2, 2049)
        with self.assertRaises(ValueError):
            psx_arc(data)

    def test_psx_arc_preserves_duplicate_types_by_index(self):
        data = bytearray(6144)
        struct.pack_into('<IIIIII', data, 0, 2, 6144, 6, 2, 6, 4)
        entries = psx_arc(data)
        self.assertEqual([(e['index'],e['offset'],e['size']) for e in entries],
                         [(0,2048,2),(1,4096,4)])

    def test_mt_arc_reads_compressed_payload_and_rejects_bad_size(self):
        payload = zlib.compress(b'TEST')
        data = bytearray(88) + payload
        struct.pack_into('<4sHH', data, 0, b'ARC\0', 7, 1)
        struct.pack_into('<IIII', data, 72, 0, len(payload), 4, 88)
        self.assertEqual(mt_arc(data)['entries'][0]['size'], 4)
        struct.pack_into('<I', data, 80, 5)
        with self.assertRaises(ValueError):
            mt_arc(data)

    def test_mt_arc_rejects_overlapping_streams(self):
        payload = zlib.compress(b'TEST')
        data = bytearray(168) + payload
        struct.pack_into('<4sHH', data, 0, b'ARC\0', 7, 2)
        for pos in (72,152):
            struct.pack_into('<IIII', data, pos, 0, len(payload), 4, 168)
        with self.assertRaises(ValueError):
            mt_arc(data)


if __name__ == '__main__':
    unittest.main()
