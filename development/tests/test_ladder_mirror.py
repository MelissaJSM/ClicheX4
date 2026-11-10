import unittest
import numpy as np
from scripts.prepare_shibuki_ladder import mirror_canvas

class LadderMirrorTests(unittest.TestCase):
    def test_origin_center_between_pixels(self):
        body=np.zeros((80,96),np.uint8);body[23,32]=5;body[43,57]=9
        mirrored=mirror_canvas(body,-16)
        self.assertEqual(mirrored[23,63],5);self.assertEqual(mirrored[43,38],9)
        np.testing.assert_array_equal(mirror_canvas(mirrored,-16),body)

    def test_origin_center_on_pixel(self):
        body=np.zeros((80,96),np.uint8);body[23,32]=5;body[43,57]=9
        mirrored=mirror_canvas(body,-15)
        self.assertEqual(mirrored[23,64],5);self.assertEqual(mirrored[43,39],9)
        np.testing.assert_array_equal(mirror_canvas(mirrored,-15),body)

    def test_visible_outside_canvas_rejected(self):
        body=np.zeros((80,96),np.uint8);body[23,0]=5
        with self.assertRaisesRegex(ValueError,'outside canvas'):mirror_canvas(body,-15)

    def test_transparent_canvas_can_cross_boundary(self):
        body=np.zeros((80,96),np.uint8)
        np.testing.assert_array_equal(mirror_canvas(body,-15),body)

if __name__=='__main__':unittest.main()
