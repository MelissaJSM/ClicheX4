import unittest

from src.psx_sector import edc, rebuild_checks, replace_payload, validate_checks


class SectorTests(unittest.TestCase):
    @staticmethod
    def raw():
        return b'\0'+b'\xff'*10+b'\0'+bytes([0,2,0,2])+bytes([0,0,8,0])*2+bytes(2328)

    def test_edc_known_short_vector(self):
        self.assertEqual(edc(b'\x01'),0x90910101)

    def test_payload_edit_preserves_headers_and_detects_corruption(self):
        raw=rebuild_checks(self.raw())
        self.assertEqual(replace_payload(raw,bytes(2048)),raw)
        edited=replace_payload(raw,b'X'+bytes(2047))
        self.assertEqual(edited[:24],raw[:24])
        self.assertEqual(edited[25:2072],raw[25:2072])
        self.assertNotEqual(edited[2072:],raw[2072:])
        validate_checks(edited)
        bad=bytearray(edited);bad[77]=1
        with self.assertRaises(ValueError):validate_checks(bad)

    def test_refuse_form2_and_wrong_size(self):
        raw=bytearray(self.raw());raw[18]|=32;raw[22]|=32
        with self.assertRaises(ValueError):rebuild_checks(raw)
        with self.assertRaises(ValueError):rebuild_checks(raw[:-1])
        with self.assertRaises(ValueError):replace_payload(rebuild_checks(self.raw()),bytes(2047))


if __name__=='__main__':unittest.main()
