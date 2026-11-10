import unittest
import numpy as np
from scripts.prepare_shibuki_armor_motion import identical,variants
from src.psx_player import indexed_atlas


def render(raw,count,records):
    atlas,_,_=indexed_atlas(raw,count)
    canvas=np.zeros((160,160),np.uint8)
    for tile,left,top in records:
        for y in range(16):
            for x in range(16):
                value=atlas[(tile//16*16+y)*256+tile%16*16+x]
                if value:canvas[top+y,left+x]=value
    return canvas


class ArmorMotionLayoutTest(unittest.TestCase):
    def test_two_arm_poses_share_far_sleeve_without_cross_contamination(self):
        raw=bytes([0x77])*6*128
        a=np.zeros((160,160),np.uint8);b=a.copy()
        a[70:77,62:67]=3;b[73:79,60:68]=5
        a[71:79,89:95]=7;b[71:79,89:95]=7
        result,ra,rb=variants(raw,6,a,b,{1,2,3},2,2)
        self.assertTrue(np.array_equal(render(result,6,ra),a))
        self.assertTrue(np.array_equal(render(result,6,rb),b))
        old,_,_=indexed_atlas(raw,6);new,_,_=indexed_atlas(result,6)
        for t in (0,4,5):
            for y in range(16):
                pos=y*256+t*16
                self.assertEqual(new[pos:pos+16],old[pos:pos+16])

    def test_only_page_edge_tile_keeps_transparent_guard_column(self):
        target=np.zeros((160,160),np.uint8);target[70:80,65:73]=3
        raw,records=identical(bytes(128),1,target,{0},1)
        self.assertTrue(np.array_equal(render(raw,1,records),target))
        atlas,_,_=indexed_atlas(raw,1)
        self.assertTrue(all(atlas[y*256]==0 for y in range(16)))

    def test_insufficient_parts_reject_without_silently_cutting_pixels(self):
        a=np.zeros((160,160),np.uint8);b=a.copy()
        a[65:71,60:86]=3;b[64:72,62:90]=7
        with self.assertRaises(ValueError):variants(bytes(256),2,a,b,{0,1},1,1)


if __name__=='__main__':unittest.main()
