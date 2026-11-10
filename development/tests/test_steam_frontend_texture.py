import struct
import unittest

import numpy as np
from PIL import Image
from src.steam_frontend_texture import info, decode, encode_blocks, replace_region


def texture(im, fmt=42):
    return (bytes.fromhex('54455800a1800020') + struct.pack('<I', 1 | im.width << 6 | im.height << 19)
            + bytes([1, fmt, 1, 0]) + struct.pack('<I', 20) + encode_blocks(im, fmt))


class FrontendTextureTests(unittest.TestCase):
    def test_color_channels_and_alpha(self):
        for color in [(255,0,0,255),(0,255,0,255),(0,0,255,255),(130,130,130,255),(0,0,0,0)]:
            raw=texture(Image.new('RGBA',(4,4),color))
            result=np.array(decode(raw))[0,0].astype(int)
            self.assertLessEqual(int(np.max(np.abs(result-np.array(color)))),12)

    def test_preserves_unrelated_blocks(self):
        raw=texture(Image.new('RGBA',(16,16),(60,80,120,255)))
        changed=replace_region(raw,(4,4,8,8),Image.new('RGBA',(4,4),(220,100,40,255)))
        offset=20+5*16
        self.assertEqual(raw[:offset],changed[:offset])
        self.assertEqual(raw[offset+16:],changed[offset+16:])
        self.assertNotEqual(raw[offset:offset+16],changed[offset:offset+16])

    def test_multicolor_cutout_keeps_transparent_pixels_clear(self):
        a=np.zeros((8,8,4),np.uint8)
        for y in range(8):
            for x in range(8):
                if x>=y//2+1:a[y,x]=[(x*61)%256,(y*83)%256,200,255]
        out=np.array(decode(texture(Image.fromarray(a))))
        self.assertTrue(np.all(out[:,:,3][a[:,:,3]==0]==0))
        self.assertTrue(np.all(out[:,:,3][a[:,:,3]==255]==255))

    def test_edge_coverage_retains_four_antialias_levels(self):
        a=np.zeros((4,4,4),np.uint8)
        a[:,:,:3]=[180,130,220]
        a[:,:,3]=np.array([0,85,170,255],np.uint8)[None,:]
        out=np.array(decode(texture(Image.fromarray(a))))
        self.assertTrue(np.array_equal(out[:,:,3],a[:,:,3]))
        self.assertLessEqual(int(np.abs(out[:,:,:3].astype(int)-a[:,:,:3]).max()),12)

    def test_rejects_bad_dimensions_format_and_size(self):
        raw=texture(Image.new('RGBA',(8,8)))
        for invalid in [raw[:-1],raw+b'\0',raw[:13]+b'\xff'+raw[14:]]:
            with self.assertRaises(ValueError):info(invalid)
        for rect in [(1,0,5,4),(4,4,12,12),(-4,0,0,4)]:
            with self.assertRaises(ValueError):replace_region(raw,rect,Image.new('RGBA',(4,4)))


if __name__=='__main__':unittest.main()
