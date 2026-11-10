import unittest
from src.rin_effects import arrival_flash,departure_flash,ice_flash


class RinEffectTests(unittest.TestCase):
    def test_arrival_uses_silver_white_not_cyan_eye(self):
        body=(bytes([15]),(1,1))
        flash,_=arrival_flash(body,(0,0,1,1),(5,5),(-2,-2,3,3),247)
        self.assertEqual(set(flash),{0,10,11})
        self.assertEqual(flash[12],11)
        self.assertEqual(arrival_flash(body,(0,0,1,1),(1,1),(0,0,1,1),248)[0],bytes([11]))

    def test_departure_keeps_body_cyan_until_pale_phase(self):
        body=(bytes([15,12]),(2,1))
        a,_=departure_flash(body,(4,-2,6,-1),(6,5),(2,-4,8,1),7)
        self.assertEqual(a[2*6+2:2*6+4],bytes([15,12]))
        self.assertEqual(a[2*6+1],11)
        b,_=departure_flash(body,(4,-2,6,-1),(6,5),(2,-4,8,1),8)
        self.assertEqual(set(b),{0,10,11})

    def test_no_silent_cropping_or_unknown_palette(self):
        for f,phase in ((arrival_flash,247),(departure_flash,7)):
            with self.subTest(f=f),self.assertRaisesRegex(ValueError,'escaped'):
                f((bytes([4]),(1,1)),(0,0,1,1),(1,1),(0,0,1,1),phase)
        with self.assertRaisesRegex(ValueError,'Invalid'):
            departure_flash((bytes([16]),(1,1)),(0,0,1,1),(5,5),(-2,-2,3,3),7)

    def test_ice_flash_preserves_silhouette_in_rin_palette(self):
        pixels=bytes([0,0,0,0,0,0,5,5,5,0,0,5,15,5,0,0,5,5,5,0,0,0,0,0,0])
        result,size=ice_flash((pixels,(5,5)))
        self.assertEqual(size,(5,5));self.assertEqual([bool(v) for v in result],[bool(v) for v in pixels])
        self.assertEqual(result[12],10);self.assertEqual(result[6],11);self.assertEqual(set(result),{0,10,11})


if __name__=='__main__':unittest.main()
