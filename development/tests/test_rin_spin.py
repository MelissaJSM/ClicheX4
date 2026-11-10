import unittest
import numpy as np
from PIL import Image
from src.rin_spin import validate_rotation
from src.psx_air_spin import ROTATING


class RinSpinTests(unittest.TestCase):
    def frames(self):
        a=np.zeros((192,192),np.uint8);a[87:100,92:98]=11;a[91,93]=15;a[99:105,98:103]=5
        frames={};bounds={}
        for i,n in enumerate(ROTATING):
            b=np.array(Image.fromarray(a).rotate(i*45,Image.Resampling.NEAREST,center=(96,96)))[72:120,72:120];frames[n]=(b.tobytes(),(48,48));bounds[n]=(-24,-24,24,24)
        return frames,bounds

    def test_full_rotation_preserves_common_center(self):
        f,b=self.frames();r=validate_rotation(f,b);self.assertEqual(len(r),8);self.assertEqual(r['175']['degrees'],315)

    def test_one_phase_origin_shift_is_rejected(self):
        f,b=self.frames();b[165]=(-23,-24,25,24)
        with self.assertRaisesRegex(ValueError,'rotation center'):validate_rotation(f,b)

    def test_one_phase_color_or_scale_edit_is_rejected(self):
        f,b=self.frames();data=bytearray(f[169][0]);data[next(i for i,v in enumerate(data) if v)]=14;f[169]=(bytes(data),(48,48))
        with self.assertRaisesRegex(ValueError,'pixels'):validate_rotation(f,b)


if __name__=='__main__':unittest.main()
