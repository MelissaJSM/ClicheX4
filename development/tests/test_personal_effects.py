import hashlib
import struct
import tempfile
import unittest
from pathlib import Path

from src.psx_personal_effects import OLD_TRAIL, recolor_stage, trail_palette
from src.psx_disc import write_archive_copies
from tests import test_psx_disc


class PersonalEffectsTests(unittest.TestCase):
    def fixture(self):
        data = bytearray(6144)
        struct.pack_into('<4I', data, 0, 1, 6144, 5, 4096)
        data[2464:2560] = OLD_TRAIL
        palette = struct.pack('<16H', *([0] * 10 + [0xdf6b] + [0] * 5))
        return bytes(data), palette

    def test_only_three_cluts_change_and_keep_transparency(self):
        arc, pal = self.fixture()
        new = recolor_stage(arc, hashlib.sha256(arc).hexdigest(), pal)
        self.assertEqual(new[:2464], arc[:2464])
        self.assertEqual(new[2560:], arc[2560:])
        for row in range(3):
            words = struct.unpack_from('<16H', new, 2464 + row * 32)
            self.assertEqual(words[0], 0)
            self.assertEqual(len(set(words[1:])), 1)
            self.assertTrue(words[1] & 0x8000)
            self.assertGreater(words[1] >> 5 & 31, words[1] & 31)

    def test_wrong_hash_non_trail_stage_and_repeat_are_rejected(self):
        arc, pal = self.fixture()
        with self.assertRaisesRegex(ValueError, 'hash'):
            recolor_stage(arc, '0' * 64, pal)
        new = recolor_stage(arc, hashlib.sha256(arc).hexdigest(), pal)
        for invalid in (new, arc[:2464] + bytes(96) + arc[2560:]):
            with self.assertRaisesRegex(ValueError, 'afterimage'):
                recolor_stage(invalid, hashlib.sha256(invalid).hexdigest(), pal)

    def test_invalid_mint_input_rejected(self):
        for pal in (bytes(31), bytes(33), bytes(32)):
            with self.assertRaises(ValueError):
                trail_palette(pal)

    def test_rin_blue_reference_is_explicit_and_preserves_default(self):
        _,pal=self.fixture();p=bytearray(pal);struct.pack_into('<H',p,12,0x7e09)
        self.assertEqual(trail_palette(p),trail_palette(pal))
        blue=trail_palette(p,reference_index=6)
        for row in range(3):
            values=struct.unpack_from('<16H',blue,row*32)
            self.assertEqual(values[0],0)
            self.assertGreater(values[1]>>10&31,values[1]>>5&31)
            self.assertTrue(values[1]&0x8000)
        for invalid in (0,16):
            with self.assertRaises(ValueError):trail_palette(p,reference_index=invalid)

    def test_multiple_archives_keep_source_and_unselected_sector(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, rec, _, raw = test_psx_disc.DiscWriteTests().fixtures(root)
            source.write_bytes(raw * 3)
            digest = hashlib.sha256(raw * 3).hexdigest()
            result = write_archive_copies(source, root / 'out.bin',
                [(rec, b'A' + bytes(2047)), ({**rec, 'lba': 2}, b'B' + bytes(2047))], digest)
            self.assertEqual([r['lba'] for r in result['changed_sectors']], [0, 2])
            self.assertEqual((root / 'out.bin').read_bytes()[2352:4704], raw)
            self.assertEqual(source.read_bytes(), raw * 3)

    def test_overlap_and_late_invalid_archive_fail_before_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, rec, _, raw = test_psx_disc.DiscWriteTests().fixtures(root)
            source.write_bytes(raw * 2)
            digest = hashlib.sha256(raw * 2).hexdigest()
            for second in (rec, {**rec, 'lba': 1, 'sha256': '0' * 64}):
                with self.assertRaises(ValueError):
                    write_archive_copies(source, root / 'bad.bin',
                        [(rec, b'A' + bytes(2047)), (second, bytes(2048))], digest)
                self.assertFalse((root / 'bad.bin').exists())


if __name__ == '__main__':
    unittest.main()
