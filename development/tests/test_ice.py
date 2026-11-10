import unittest
from src.psx_ice import flash_from_recovery,validate_flash

class IceFlashTests(unittest.TestCase):
    def test_flash_retains_silhouette_with_inward_contour(self):
        body=bytes([0]*5+[0,4,4,4,0]*3+[0]*5)
        flash,size=flash_from_recovery(body,(5,5))
        self.assertEqual([bool(v) for v in body],[bool(v) for v in flash])
        self.assertEqual(flash[12],12)
        self.assertEqual(flash[6],15)
        self.assertEqual(set(flash),{0,12,15})
        self.assertTrue(validate_flash({87:(body,(5,5)),88:(flash,size)},{87:(-2,-2,3,3),88:(-2,-2,3,3)})['silhouette_equal'])

    def test_flash_pixel_and_origin_changes_rejected(self):
        body=bytes([4]*9);flash,size=flash_from_recovery(body,(3,3))
        modified=bytes([0])+flash[1:]
        with self.assertRaisesRegex(ValueError,'silhouette'):
            validate_flash({87:(body,size),88:(modified,size)},{87:(0,0,3,3),88:(0,0,3,3)})
        with self.assertRaisesRegex(ValueError,'silhouette'):
            validate_flash({87:(body,size),88:(flash,size)},{87:(0,0,3,3),88:(1,0,4,3)})
        with self.assertRaisesRegex(ValueError,'dimensions'):flash_from_recovery(body,(2,3))

if __name__=='__main__':unittest.main()
