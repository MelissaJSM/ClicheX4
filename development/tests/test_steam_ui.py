import struct
import unittest

from src.steam_arc import pat_from_ps1
from src.steam_ui import stage_texture,pat_frames


class SteamUiTests(unittest.TestCase):
    def test_page_boundary_and_padding_preservation(self):
        # A native vertical page boundary becomes a horizontal PC boundary.
        tex=bytearray(b'TEX\0'+bytes(16)+bytes([0xcd])*(2048*2048))
        struct.pack_into('<I',tex,8,1|(2048<<6)|(2048<<19));tex[13]=0x12
        struct.pack_into('<I',tex,16,20)
        packed=bytes(256*128)+bytes([0x21])*(16*128)
        for y in range(256):tex[20+y*2048:20+y*2048+256]=bytes(256)
        for y in range(16):tex[20+y*2048+256:20+y*2048+512]=bytes([1,2])*128
        new=bytearray(packed);new[256*128]=0x43
        result=stage_texture(bytes(tex),packed,bytes(new))
        self.assertEqual(result[20+256:20+260],bytes([3,4,1,2]))
        self.assertEqual([i for i,(a,b) in enumerate(zip(tex,result)) if a!=b],[276,277])
        self.assertEqual(stage_texture(bytes(tex),packed,packed),bytes(tex))
        broken=bytearray(tex);broken[276]=9
        with self.assertRaises(ValueError):stage_texture(bytes(broken),packed,bytes(new))
        with self.assertRaises(ValueError):stage_texture(bytes(tex),packed,bytes(new)+b'\0')

    def test_shared_frame_reference_and_corruption(self):
        quad=bytes([0xc1,0x23,0xf0,0x10])
        source=struct.pack('<IHHHH',4,1,2,1,2)+quad
        pat=pat_from_ps1(source)
        self.assertEqual(pat_frames(pat),[[quad,quad]])
        corrupted=bytearray(pat);struct.pack_into('<I',corrupted,16,7)
        with self.assertRaises(ValueError):pat_frames(corrupted)
        with self.assertRaises(ValueError):pat_frames(pat+b'\0')


if __name__=='__main__':unittest.main()
