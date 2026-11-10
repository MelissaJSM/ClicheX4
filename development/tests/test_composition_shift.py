import struct
import unittest
from src.psx_composition_shift import translate_compositions
from src.psx_player import composition_frame


def fixture(shared=False, x=5):
    # Two frames, two parts each, optionally referring to the same records.
    return (struct.pack('<3I', 4, 0x20002, (0x20002 if shared else 0x40002))
            + struct.pack('<BBbb', 0x40, 7, x, -20)
            + struct.pack('<BBbb', 0, 8, x + 16, -4)
            + struct.pack('<BBbb', 0, 9, -10, 12)
            + struct.pack('<BBbb', 0, 10, 6, 12))


class CompositionShiftTests(unittest.TestCase):
    def test_whole_frame_translation_preserves_other_fields_and_frames(self):
        old = fixture()
        new, report = translate_compositions(old, {(0, 0): (-8, 0)})
        self.assertEqual(report['changed_bytes'], 2)
        self.assertEqual(composition_frame(new, 0, 1), composition_frame(old, 0, 1))
        for a, b in zip(composition_frame(old, 0, 0)['parts'], composition_frame(new, 0, 0)['parts']):
            self.assertEqual(b, {**a, 'x': a['x'] - 8})
        restored, _ = translate_compositions(new, {(0, 0): (8, 0)})
        self.assertEqual(restored, old)

    def test_shared_records_require_all_owners_and_equal_shift(self):
        old = fixture(shared=True)
        for shifts in ({(0, 0): (-8, 0)}, {(0, 0): (-8, 0), (0, 1): (-7, 0)}):
            with self.assertRaisesRegex(ValueError, 'shared'):
                translate_compositions(old, shifts)
        new, report = translate_compositions(old, {(0, 0): (-8, 0), (0, 1): (-8, 0)})
        self.assertEqual(report['changed_bytes'], 2)
        self.assertEqual(composition_frame(new, 0, 1)['parts'][0]['x'], -3)

    def test_out_of_range_and_nonexistent_selection_are_rejected(self):
        for shifts in ({(0, 0): (-140, 0)}, {(0, 0): (0, 150)}, {(0, 2): (-8, 0)}, {}):
            with self.assertRaises(ValueError):
                translate_compositions(fixture(), shifts)


if __name__ == '__main__':
    unittest.main()
