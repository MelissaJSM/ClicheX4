import unittest
import numpy as np
from scripts.prepare_shibuki_armor_remaining import pack_many
from src.psx_player import indexed_atlas

def render(raw,count,records):
    atlas,_,_=indexed_atlas(raw,count);out=np.zeros((160,160),np.uint8)
    for tile,left,top,flag in records:
        for y in range(16):
            for x in range(16):
                value=atlas[(tile//16*16+y)*256+tile%16*16+x]
                if value:out[top+(15-y if flag&128 else y),left+(15-x if flag&64 else x)]=value
    return out

class ArmorRemainingLayoutTest(unittest.TestCase):
    def test_three_translated_and_mirrored_poses_share_one_tile(self):
        a=np.zeros((160,160),np.uint8);a[65:70,70:74]=3;a[70:73,70:72]=7
        b=np.roll(a,8,axis=1);c=np.roll(a[:,::-1],3,axis=0)
        original=bytes([0x55])*3*128
        raw,records=pack_many(original,3,[a,b,c],{1},[1,1,1])
        for target,parts in zip((a,b,c),records):self.assertTrue(np.array_equal(render(raw,3,parts),target))
        before,_,_=indexed_atlas(original,3);after,_,_=indexed_atlas(raw,3)
        for tile in (0,2):
            for y in range(16):self.assertEqual(before[y*256+tile*16:y*256+tile*16+16],after[y*256+tile*16:y*256+tile*16+16])

    def test_page_edge_translation_preserves_guard_column(self):
        a=np.zeros((160,160),np.uint8);a[65:72,70:76]=3
        b=np.roll(a,4,axis=1)
        raw,records=pack_many(bytes(128),1,[a,b],{0},[1,1])
        for target,parts in zip((a,b),records):self.assertTrue(np.array_equal(render(raw,1,parts),target))
        atlas,_,_=indexed_atlas(raw,1);self.assertTrue(all(atlas[y*256]==0 for y in range(16)))

    def test_different_large_layers_cannot_overwrite_one_tile(self):
        a=np.zeros((160,160),np.uint8);a[60:76,60:76]=3;b=a.copy();b[60:76,60:76]=7
        with self.assertRaises(ValueError):pack_many(bytes(256),2,[a,b],{1},[1,1])

if __name__=='__main__':unittest.main()
