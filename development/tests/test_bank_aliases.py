"""X의 중복 뱅크 주소를 명시적으로 허용할 때만 읽는다."""
import struct
import unittest

from src.psx_player import bank_offsets, graphics_bank


class BankAliasTests(unittest.TestCase):
    def sample(self):
        # IDs 0/1 share a bank, ID 2 starts a different bank.
        return struct.pack('<3I', 12, 12, 24) + struct.pack('<I', 1 << 20 | 4) + bytes(8) + struct.pack('<I', 1 << 20 | 4) + bytes(8)

    def test_opt_in_and_next_distinct_boundary(self):
        data = self.sample()
        with self.assertRaises(ValueError):
            bank_offsets(data)
        with self.assertRaises(ValueError):
            graphics_bank(data, 0)
        a = graphics_bank(data, 0, allow_bank_aliases=True)
        b = graphics_bank(data, 1, allow_bank_aliases=True)
        self.assertEqual(a, b)
        self.assertEqual((a['base'], a['end']), (12, 24))
        self.assertEqual(a['frames'][0]['limit'], 24)
        self.assertEqual(graphics_bank(data, 2, allow_bank_aliases=True)['end'], len(data))

    def test_alias_opt_in_still_rejects_invalid_directory(self):
        for offsets in ((12, 24, 12), (12, 12, 100), (12, 12, 25), (12, 8, 24)):
            data = struct.pack('<3I', *offsets) + self.sample()[12:]
            with self.assertRaises(ValueError):
                bank_offsets(data, allow_aliases=True)


if __name__ == '__main__':
    unittest.main()
