import unittest
from src.psx_tile_layout import pack_rectangles
from src.psx_player import indexed_atlas,compose_indices

class TileLayoutTests(unittest.TestCase):
    def test_overlap_has_single_owner_and_unselected_tiles_survive(self):
        old=bytes([0x76])*512
        canvas=bytes((x+y)%15+1 for y in range(16) for x in range(24))
        result=pack_rectangles(old,4,canvas,(24,16),[(0,0),(8,0)],[1,2],{0,1,2})
        def part(t,x):return dict(index=t,tile=t,x=x,y=0,page=0,clut=0,unknown_flags=0,flip_x=False,flip_y=False)
        comp={'parts':[part(1,0),part(2,8)]}
        self.assertEqual(compose_indices(result,4,comp)[0],canvas)
        a,_,_=indexed_atlas(old,4);b,_,_=indexed_atlas(result,4)
        for y in range(16):
            self.assertEqual(a[y*256+48:y*256+64],b[y*256+48:y*256+64])
            self.assertEqual(b[y*256:y*256+16],bytes(16))
            self.assertEqual(b[y*256+32:y*256+40],bytes(8))
        self.assertEqual(old,bytes([0x76])*512)

    def test_uncovered_opaque_pixels_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'not covered'):
            pack_rectangles(bytes(384),3,bytes([2])*384,(24,16),[(0,0)],[1],{0,1})

    def test_invalid_and_unsafe_assignments_rejected(self):
        cases=[(bytes([16])*256,(16,16),[(0,0)],[1],{1}),
               (bytes(256),(16,16),[(1,0)],[1],{1}),
               (bytes([1])*256,(16,16),[(0,0)],[0],{0}),
               (bytes(256),(16,16),[(0,0)],[1],{2}),
               (bytes(256),(16,16),[(0,0),(0,0)],[1,1],{1})]
        for pixels,size,rects,ids,clear in cases:
            with self.subTest(ids=ids,rects=rects):
                with self.assertRaises(ValueError):pack_rectangles(bytes(384),3,pixels,size,rects,ids,clear)

if __name__=='__main__':unittest.main()
