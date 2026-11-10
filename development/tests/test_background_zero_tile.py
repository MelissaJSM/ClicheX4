import struct
import unittest
import numpy as np
from scripts.prepare_riko_illustrations import background_replace
from scripts.prepare_riko_ui import entry
from scripts.inventory_shibuki_ui import background

def archive(blank_tile):
    chunks=[(0x10000,bytes(2048)),(0,bytes(1024)),(1,struct.pack('<III',blank_tile<<16,0,0))]
    result=bytearray(2048)
    for i,(kind,data) in enumerate(chunks):
        struct.pack_into('<II',result,8+i*8,kind,len(data));result+=data+bytes(-len(data)%2048)
    struct.pack_into('<II',result,0,len(chunks),len(result))
    return bytes(result)

class BackgroundZeroTileTests(unittest.TestCase):
    def check_blank(self,blank_tile):
        raw=archive(blank_tile);picture=np.zeros((256,256),np.uint8);picture[:16,:16]=1
        palette=struct.pack('<16H',0,*([32767]*15))*128
        expected=background(raw,palette,1)
        new,_=background_replace(raw,[0],picture,80,preserve_zero_tile=True)
        self.assertEqual(background(new,palette,1).tobytes(),expected.tobytes())
        self.assertIsNone(background(new,palette,1).getbbox())
        self.assertEqual(background(new,palette,0).getbbox(),(0,0,16,16))
        self.assertEqual(entry(raw,1)[:4],entry(new,1)[:4])
        self.assertEqual(len(new),len(raw))

    def test_blank_background_survives_new_opaque_tile(self):self.check_blank(0)
    def test_blank_map_can_point_to_nonzero_texture_tile(self):self.check_blank(3)

if __name__=='__main__':unittest.main()
