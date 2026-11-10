import copy
import unittest
from src.sprite_sheet import pack_frames,unpack_frames


class SpriteSheetTests(unittest.TestCase):
    def fixture(self):
        return {'pose_a':(bytes([0,1,2,0,3,4]),(3,2),(-2,-1,1,1)),
                'pose_b':(bytes([5,0,6,7]),(2,2),(1,-2,3,0))}

    def test_negative_world_coordinates_and_transparency_roundtrip(self):
        frames=self.fixture();pixels,layout=pack_frames(frames,columns=2,cell=(8,8),origin=(4,4))
        self.assertEqual(unpack_frames(pixels,layout['size'],layout),{k:(v[0],v[1]) for k,v in frames.items()})
        self.assertEqual(layout['frames'][0]['rect'],[2,3,3,2])
        self.assertEqual(layout['frames'][1]['rect'],[13,2,2,2])

    def test_padding_ink_and_resized_sheets_are_rejected(self):
        pixels,layout=pack_frames(self.fixture(),cell=(8,8),origin=(4,4))
        bad=bytearray(pixels);bad[0]=1
        with self.assertRaisesRegex(ValueError,'outside native'):unpack_frames(bad,layout['size'],layout)
        with self.assertRaisesRegex(ValueError,'dimensions'):unpack_frames(pixels,(1,len(pixels)),layout)
        bad=bytearray(pixels);bad[layout['frames'][0]['rect'][1]*layout['size'][0]+2]=16
        with self.assertRaisesRegex(ValueError,'4bpp'):unpack_frames(bad,layout['size'],layout)

    def test_duplicate_overlapping_and_outside_metadata_rejected(self):
        pixels,layout=pack_frames(self.fixture(),columns=2,cell=(8,8),origin=(4,4))
        for mode in ('duplicate','overlap','outside'):
            bad=copy.deepcopy(layout)
            if mode=='duplicate':bad['frames'][1]['key']=bad['frames'][0]['key']
            elif mode=='overlap':bad['frames'][1]['rect']=bad['frames'][0]['rect'][:]
            else:bad['frames'][1]['rect'][0]=-1
            with self.subTest(mode=mode),self.assertRaises(ValueError):unpack_frames(pixels,layout['size'],bad)

    def test_oversize_frame_is_not_silently_cropped_or_resized(self):
        with self.assertRaisesRegex(ValueError,'fixed cell'):
            pack_frames(self.fixture(),cell=(2,2),origin=(0,0))


if __name__=='__main__':unittest.main()
