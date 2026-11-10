import unittest
import numpy as np
from src.rin_registration import align_contact_x,contact_span

class ContactRegistrationTests(unittest.TestCase):
    def test_ribbon_width_does_not_move_ground_anchor(self):
        a=np.zeros((70,100),np.uint8);a[20:60,35:40]=5;a[57:60,60:65]=11;a[5:15,5:90]=7
        before=a.copy();b,r=align_contact_x(a,-1.5,origin=50)
        self.assertEqual(r['translate_x'],-1)
        self.assertEqual(contact_span(b,50)['center_x'],-1.5)
        self.assertTrue(np.array_equal(a,before))
        self.assertTrue(np.array_equal(np.bincount(a.ravel()),np.bincount(b.ravel())))
        self.assertEqual(contact_span(b,50)['floor_y'],9)

    def test_ground_hand_between_boots_does_not_shift_center(self):
        a=np.zeros((64,96),np.uint8);a[59:62,20:28]=1;a[59:62,60:70]=1;a[59:62,38:45]=11
        b,r=align_contact_x(a,0,origin=48)
        self.assertLessEqual(abs(contact_span(b,48)['center_x']),.5)
        self.assertEqual(np.count_nonzero(a),np.count_nonzero(b))

    def test_crop_and_empty_refused(self):
        a=np.zeros((20,20),np.uint8);a[3:18,1:3]=5
        with self.assertRaises(ValueError):align_contact_x(a,-40,10)
        with self.assertRaises(ValueError):contact_span(np.zeros((4,4),np.uint8))

if __name__=='__main__':unittest.main()
