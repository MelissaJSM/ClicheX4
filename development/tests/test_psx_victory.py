import unittest
from src.psx_victory import departure_flash


class VictoryTests(unittest.TestCase):
    def test_departure_follows_new_body_and_preserves_world_origin(self):
        body = (bytes([0,4,0,0,12,0]), (3,2))
        data, size = departure_flash(body, (7,-4,10,-2), (7,6), (5,-6,12,0), 7)
        self.assertEqual(size, (7,6))
        self.assertEqual(data[2*7+3],4)
        self.assertEqual(data[3*7+3],12)
        self.assertEqual(data[2*7+2],15)
        self.assertEqual(data[2*7+1],0)
        pale, _ = departure_flash(body, (7,-4,10,-2), (7,6), (5,-6,12,0), 8)
        self.assertEqual(pale[2*7+3],15)
        self.assertEqual(pale[2*7+1],12)
        self.assertEqual(set(pale), {0,12,15})

    def test_departure_refuses_clipped_cloak_and_invalid_source(self):
        with self.assertRaisesRegex(ValueError,'escaped'):
            departure_flash((bytes([4]),(1,1)), (0,0,1,1), (1,1), (0,0,1,1), 7)
        for body,phase in [((b'\x10',(1,1)),7),((b'\x04',(2,1)),7),((b'\x04',(1,1)),9)]:
            with self.subTest(body=body,phase=phase),self.assertRaisesRegex(ValueError,'Invalid'):
                departure_flash(body,(0,0,1,1),(5,5),(-2,-2,3,3),phase)


if __name__=='__main__':unittest.main()
