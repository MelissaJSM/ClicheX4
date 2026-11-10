import unittest
import numpy as np
from src.psx_sprite_batch import canvas_from_parts,pack_original_layout,recolor_tiles,inherited_recolored_part
from src.psx_paired_layout import pack_variant_pair
from src.psx_player import indexed_atlas

def part(tile,x,y,flip=False):
    return dict(index=0,tile=tile,x=x,y=y,flip_x=flip,flip_y=False,page=0,clut=0,unknown_flags=0)

class SpriteBatchTests(unittest.TestCase):
    def test_boundary_exception_requires_original_shape_and_part(self):
        p=part(0,2,3,True)
        self.assertTrue(inherited_recolored_part(bytes([0,3,3,5]),bytes([0,8,8,9]),p,p))
        self.assertFalse(inherited_recolored_part(bytes([0,3,3,5]),bytes([1,8,8,9]),p,p))
        self.assertFalse(inherited_recolored_part(bytes([0,3,3,5]),bytes([0,8,9,9]),p,p))
        self.assertFalse(inherited_recolored_part(bytes([0,3,3,5]),bytes([0,8,8,9]),p,part(0,3,3,True)))
    def test_large_canvas_pair_roundtrip_and_other_tiles_preserved(self):
        a=np.zeros((160,160),np.uint8);a[30:40,50:60]=5;b=a.copy();b[70:74,90:99]=7
        raw=bytes([0xAA])*512
        result,rp,sp,_,_=pack_variant_pair(raw,4,a,b,[[49,29]],[],[[89,69]],{0,1,2})
        for rows,want in ((rp,a),(sp,b)):
            cp={'parts':[part(t,x-80,y-80) for t,x,y in rows]}
            self.assertTrue(np.array_equal(canvas_from_parts(result,4,cp),want))
        old,_,_=indexed_atlas(raw,4);new,_,_=indexed_atlas(result,4)
        for y in range(16):self.assertEqual(old[y*256+48:y*256+64],new[y*256+48:y*256+64])

    def test_large_canvas_rejects_outside_rectangle(self):
        a=np.zeros((160,160),np.uint8)
        with self.assertRaisesRegex(ValueError,'outside'):
            pack_variant_pair(bytes(256),2,a,a,[[150,150]],[],[],{0,1})

    def test_shared_mirrored_tile_roundtrip(self):
        cp={'parts':[part(1,-20,-10),part(1,10,-10,True)]};v=np.zeros((160,160),np.uint8)
        v[72:78,62:66]=4;v[72:78,100:104]=4
        result=pack_original_layout(bytes(256),2,v,cp,{1})
        self.assertTrue(np.array_equal(canvas_from_parts(result,2,cp),v))

    def test_shared_tile_conflict_is_rejected(self):
        cp={'parts':[part(1,-20,-10),part(1,10,-10,True)]};v=np.zeros((160,160),np.uint8);v[72,62]=4
        with self.assertRaisesRegex(ValueError,'exactly'):pack_original_layout(bytes(256),2,v,cp,{1})

    def test_recolor_preserves_other_tile_and_alpha(self):
        raw=bytes([0x50])*256;mapping=list(range(16));mapping[5]=9
        result=recolor_tiles(raw,2,{1},mapping);a,_,_=indexed_atlas(raw,2);b,_,_=indexed_atlas(result,2)
        for y in range(16):
            self.assertEqual(a[y*256:y*256+16],b[y*256:y*256+16])
            self.assertEqual(bytes(0 if x==0 else 9 for x in a[y*256+16:y*256+32]),b[y*256+16:y*256+32])
        mapping[5]=0
        with self.assertRaises(ValueError):recolor_tiles(raw,2,{1},mapping)

    def test_canvas_visible_overflow_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'outside'):
            canvas_from_parts(bytes([0x11])*128,1,{'parts':[part(0,-100,-100)]})

if __name__=='__main__':unittest.main()
