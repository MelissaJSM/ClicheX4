import unittest
from src.sprite_scale import validate_fixed_reference,validate_reference_views

class SpriteScaleTests(unittest.TestCase):
    def test_view_assignments_cannot_skip_or_switch_reference(self):
        views={'front':(bytes([1,2]),(2,1),(0,0,2,1)),
               'side':(bytes([3,4]),(2,1),(0,0,2,1))}
        frames={35:(bytes([1,2]),(2,1)),39:(bytes([3,4]),(2,1))}
        bounds={35:(0,0,2,1),39:(0,0,2,1)};positions={'35':[0,0],'39':[0,0]}
        result=validate_reference_views(frames,bounds,views,{'35':'front','39':'side'},positions)
        self.assertEqual(result['checked_frames'],[35,39])
        for assignment in ({'35':'front'},{'35':'front','39':'unknown'},{'35':'side','39':'side'}):
            with self.assertRaises(ValueError):validate_reference_views(frames,bounds,views,assignment,positions)
        with self.assertRaises(ValueError):
            validate_reference_views(frames,bounds,views,{'35':'front','39':'side'},{'35':[0,0]})

    def test_cape_can_fill_transparent_corner_but_not_replace_head(self):
        ref=bytes([1,0,2,3]);bounds={7:(0,0,2,2)}
        validate_fixed_reference({7:(bytes([1,8,2,3]),(2,2))},bounds,ref,(2,2),(0,0,2,2),{'7':[0,0]})
        with self.assertRaises(ValueError):
            validate_fixed_reference({7:(bytes([8,8,2,3]),(2,2))},bounds,ref,(2,2),(0,0,2,2),{'7':[0,0]})
    def test_pose_translation_preserves_scale_even_with_different_canvas_height(self):
        ref=bytes([0,1,2,0,3,4,5,0,0,0,0,0]);pixels=bytearray(30)
        pixels[8:10]=bytes([1,2]);pixels[14:16]=bytes([4,5])
        result=validate_fixed_reference({7:(bytes(pixels),(6,5))},{7:(-3,-4,3,1)},ref,(4,3),(1,0,3,2),{'7':[-1,-3]})
        self.assertTrue(result['head_neck_pixels_exact'])

    def test_shrunk_patch_and_omitted_registration_are_rejected(self):
        ref=bytes([1,2,3,4]);frames={7:(bytes([1,1,0,0]),(2,2))};bounds={7:(0,0,2,2)}
        with self.assertRaisesRegex(ValueError,'scale or identity'):validate_fixed_reference(frames,bounds,ref,(2,2),(0,0,2,2),{'7':[0,0]})
        with self.assertRaisesRegex(ValueError,'Every motion'):validate_fixed_reference(frames,bounds,ref,(2,2),(0,0,2,2),{})

    def test_outside_patch_and_fractional_coordinates_are_rejected(self):
        ref=bytes([1,2,3,4]);frames={7:(ref,(2,2))};bounds={7:(0,0,2,2)}
        for pos in ([1,0],[.5,0]):
            with self.assertRaises(ValueError):validate_fixed_reference(frames,bounds,ref,(2,2),(0,0,2,2),{'7':pos})
