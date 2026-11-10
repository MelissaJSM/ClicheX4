import unittest
from src.psx_ui_atlas import write_tile
from src.psx_ui_render import render_static_rgba


class NativeUiPaletteTests(unittest.TestCase):
    def test_identical_indices_use_each_parts_palette(self):
        texture=bytearray(2048);write_tile(texture,0,bytes([1])*256)
        common={'page':0,'tile':0,'y':0,'flip_x':False,'flip_y':False,'unknown_flags':0}
        comp={'parts':[{**common,'x':0,'clut':0},{**common,'x':16,'clut':1}]}
        palettes={0:[0,0x801f]+[0]*14,1:[0,0x83e0]+[0]*14}
        image,bounds=render_static_rgba(bytes(texture),comp,palettes)
        self.assertEqual(bounds,(0,0,32,16))
        self.assertEqual(image.getpixel((8,8)),(255,0,0,255))
        self.assertEqual(image.getpixel((24,8)),(0,255,0,255))

    def test_missing_auxiliary_palette_is_not_silently_ignored(self):
        part={'page':0,'tile':0,'x':0,'y':0,'flip_x':False,'flip_y':False,'unknown_flags':0,'clut':1}
        with self.assertRaisesRegex(ValueError,'Missing native UI part palette'):
            render_static_rgba(bytes(2048),{'parts':[part]},{0:[0]*16})
