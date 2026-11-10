import struct
import unittest

from src.steam_dialogue import decode_dat4, encode_dat4, remap_messages


class SteamDialogueTests(unittest.TestCase):
    def test_dat4_boundaries_and_message_ids(self):
        messages = [[0x8000+i] for i in range(55)]
        raw = encode_dat4(messages)
        self.assertEqual(decode_dat4(raw), messages)
        for broken in (raw[:-1], raw+b'\0', raw[:12]+struct.pack('<I', 9000)+raw[16:]):
            with self.assertRaises(ValueError):
                decode_dat4(broken)

    def test_font_remap_preserves_every_control_bit(self):
        bitmap = bytes([14])*256
        for flags in range(0, 65536, 0x800):
            old = [[flags | 300, flags | 2047]]
            result = remap_messages(old, {300: bitmap}, {bitmap: 1014})
            self.assertEqual(result, [[flags | 1014, flags | 1023]])
        with self.assertRaises(ValueError):
            remap_messages([[300]], {300: bitmap}, {bitmap: 1024})


if __name__ == '__main__':
    unittest.main()
