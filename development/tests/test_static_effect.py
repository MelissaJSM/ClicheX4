import unittest
from src.psx_static_effect import compose_static, patch_static


def part(tile=0, x=0, flip=False):
    return {'x': x, 'y': 0, 'page': tile//256, 'tile': tile%256,
            'clut': 0, 'unknown_flags': 0, 'flip_x': flip, 'flip_y': False}


class StaticEffectTests(unittest.TestCase):
    def test_noop_preserves_unreferenced_bytes(self):
        source = bytes((i*37+9) % 256 for i in range(2048))
        c = {'parts': [part()]}
        frame = compose_static(source, c)[:2]
        self.assertEqual(patch_static(source, {23: c}, {23: frame}), source)

    def test_pixel_edit_preserves_other_nibble_and_tiles(self):
        source = bytes([0x21])*2048
        c = {'parts': [part()]}
        data, size = compose_static(source, c)[:2]
        changed = bytearray(data); changed[0] = 7
        result = patch_static(source, {23: c}, {23: (bytes(changed), size)})
        self.assertEqual(result[0], 0x27)
        self.assertEqual(result[1:], source[1:])

    def test_shared_mirrored_tile_conflict_is_rejected(self):
        source = bytes([0x21])*2048
        c = {'parts': [part(), part(x=16, flip=True)]}
        data, size = compose_static(source, c)[:2]
        changed = bytearray(data); changed[0] = 7
        with self.assertRaisesRegex(ValueError, 'Conflicting shared'):
            patch_static(source, {23: c}, {23: (bytes(changed), size)})

    def test_out_of_range_static_tile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside atlas'):
            compose_static(bytes(2048), {'parts': [part(tile=16)]})
