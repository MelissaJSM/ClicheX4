import struct
import unittest

from src.steam_menu import native_menu_frames, encode_frames
from src.steam_ui import pat_frames


class SteamMenuTests(unittest.TestCase):
    def fixture(self):
        n = 118
        frames = [struct.pack('<BBbb', 0xc1, i, -112+i, 0) for i in range(n)]
        head = b'PAT\0'+struct.pack('<III', 3, 1, n)
        counts = struct.pack('<'+'I'*n, *([1]*n))
        # Old offsets include gaps from removed label characters. Last three
        # slots were newly appended with zero legacy offsets.
        headers = b''.join(struct.pack('<HH', 1, 115+i*2 if i < 115 else 0) for i in range(n))
        return head+counts+headers+b''.join(frames), frames

    def test_stale_offsets_and_appended_slots_are_serialized(self):
        native, frames = self.fixture()
        decoded = native_menu_frames(native)
        self.assertEqual(decoded, frames)
        self.assertEqual(pat_frames(encode_frames(decoded)), [frames])
        self.assertEqual(decoded[-3:], frames[-3:])

    def test_corrupt_counts_offsets_and_tail_rejected(self):
        native, _ = self.fixture()
        for offset, value in ((16, 2), (16+118*4, 2), (16+118*4+2, 0)):
            broken = bytearray(native)
            struct.pack_into('<H', broken, offset, value)
            with self.assertRaises(ValueError):
                native_menu_frames(broken)
        with self.assertRaises(ValueError):
            native_menu_frames(native+b'\0')
        with self.assertRaises(ValueError):
            native_menu_frames(native[:-4])


if __name__ == '__main__':
    unittest.main()
