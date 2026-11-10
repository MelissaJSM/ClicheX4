import unittest
from src.psx_rakuhouha import CHARGE_BOXES,validate_charge

class RakuhouhaChargeTests(unittest.TestCase):
    def setUp(self):
        self.frames={};self.originals={};self.bounds={};self.points={}
        for n,b in CHARGE_BOXES.items():
            i=(b[1]+48)*96+b[0]+48;original=bytearray(96*96);original[i]=3
            pixels=bytearray(original);pixels[i]=6;pixels[0]=15
            self.frames[n]=(bytes(pixels),(96,96));self.originals[n]=(bytes(original),(96,96));self.bounds[n]=(-48,-48,48,48);self.points[n]=i

    def test_body_edits_outside_aura_are_allowed(self):
        self.assertEqual(validate_charge(self.frames,self.originals,self.bounds),{str(n):1 for n in CHARGE_BOXES})

    def test_missing_aura_pixel_is_rejected(self):
        pixels,size=self.frames[179];edited=bytearray(pixels);edited[self.points[179]]=0;self.frames[179]=(bytes(edited),size)
        with self.assertRaisesRegex(ValueError,'Charging aura changed'):validate_charge(self.frames,self.originals,self.bounds)

if __name__=='__main__':unittest.main()
