import copy
import unittest
import numpy as np
from src.sprite_window_fit import fit_windows

def parts(count,flip=False):
    return [dict(tile=i,x=0,y=0,flip_x=flip if i==0 else False,flip_y=False,clut=0) for i in range(count)]

class WindowFitTests(unittest.TestCase):
    def assert_covered(self,px,ps,left=0,top=0):
        before=px.copy();metadata=copy.deepcopy(ps)
        fitted=fit_windows(ps,px,left,top)
        self.assertIsNotNone(fitted)
        self.assertEqual(ps,metadata)
        self.assertTrue(np.array_equal(px,before))
        yy,xx=np.nonzero(px);covered=np.zeros(len(xx),bool)
        for p,x,y in fitted:
            x-=left;y-=top
            mask=(yy>=y)&(yy<y+16)&(xx>=x)&(xx<x+16)
            if p['tile']%16==0:
                blank=x+(15 if p['flip_x'] else 0)
                self.assertFalse(np.any(mask&(xx==blank)))
            covered|=mask
        self.assertTrue(covered.all())
        self.assertEqual({p['tile'] for p,x,y in fitted},{p['tile'] for p in ps})

    def test_offset_pose_all_pixels_and_metadata_preserved(self):
        px=np.zeros((31,30),np.uint8);px[2:28,3:27]=7;px[28:,22:25]=4
        self.assert_covered(px,parts(4),-17,-28)

    def test_horizontal_mirror_keeps_uv_zero_column_transparent(self):
        px=np.ones((16,15),np.uint8)
        self.assert_covered(px,parts(1))
        self.assert_covered(px,parts(1,True),-9,-6)

    def test_impossible_and_aliased_windows_rejected(self):
        self.assertIsNone(fit_windows(parts(1),np.ones((17,17),np.uint8),0,0,100))
        aliases=parts(2);aliases[1]['tile']=0
        self.assertIsNone(fit_windows(aliases,np.ones((4,4),np.uint8),0,0))

    def test_signed_coordinates_must_fit(self):
        self.assertIsNone(fit_windows(parts(1),np.ones((15,15),np.uint8),500,0,10))
        self.assertIsNone(fit_windows(parts(1,True),np.ones((15,15),np.uint8),500,0,10))

    def test_two_uv_edges_preserve_both_blank_columns(self):
        try:import scipy.optimize
        except ImportError:self.skipTest('Exact optional solver unavailable')
        ps=parts(2);ps[1]['tile']=16
        px=np.ones((32,15),np.uint8)
        self.assert_covered(px,ps,-12,-20)
        for p in ps:p['flip_x']=True
        self.assert_covered(px,ps,-12,-20)

if __name__=='__main__':unittest.main()
