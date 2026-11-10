import unittest
import numpy as np
from PIL import Image
from src.epsxe_state import match_sprite,framebuffer


class RenderMatchTests(unittest.TestCase):
    def test_framebuffer_matches_scalar_rgb555_with_stride_offset_and_high_bit(self):
        import struct
        prefix=32;raw=bytearray(prefix+1048576)
        for row in range(512):
            for col in range(320):
                struct.pack_into('<H',raw,prefix+row*2048+col*2,(row*320+col)&65535)
        for page in (0,256):
            expected=bytearray()
            for row in range(page,page+240):
                for col in range(320):
                    w=(row*320+col)&65535
                    expected.extend(((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31))
            self.assertEqual(framebuffer(raw,prefix,page).tobytes(),bytes(expected))

    def test_all_opaque_pixels_and_both_mirrors_remain_required(self):
        a=np.zeros((7,9,4),dtype=np.uint8)
        a[1:6,1:8]=(32,32,57,255)
        a[2,2]=(131,82,172,255);a[3,5]=(255,213,180,255)
        a[4,3]=(0,164,172,255)
        sprite=Image.fromarray(a);scene=np.full((240,320,3),32,dtype=np.uint8)
        for x,y,flip in [(21,37,False),(101,78,True)]:
            p=a[:,::-1] if flip else a;m=p[:,:,3]!=0
            target=scene[y:y+7,x:x+9];target[m]=p[:,:,:3][m]
        matches=match_sprite(Image.fromarray(scene),sprite)
        self.assertEqual({(r['x'],r['y'],r['flip_x']) for r in matches},{(21,37,False),(101,78,True)})
        # A common outline pixel is outside the three color anchors. It must
        # still invalidate an otherwise matching image.
        scene[38,22]=(1,2,3)
        matches=match_sprite(Image.fromarray(scene),sprite)
        self.assertEqual([(r['x'],r['y'],r['flip_x']) for r in matches],[(101,78,True)])

    def test_empty_sprite_is_not_evidence(self):
        self.assertEqual(match_sprite(Image.new('RGB',(320,240)),Image.new('RGBA',(4,4))),[])


if __name__=='__main__':unittest.main()
