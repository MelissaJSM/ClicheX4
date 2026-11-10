import struct,unittest
from src.psx_text import codes,rename_zero,message_ranges

class TextTests(unittest.TestCase):
    def test_names_keep_control_flags_and_directory(self):
        words=[v|flag for v,flag in zip(codes('Zero'),(0x4000,0x1000,0,0x2000))]+[511]+list(codes('ZERO'))+[0x81ff]
        data=struct.pack('<H',2)+struct.pack('<'+'H'*len(words),*words)
        result,changes=rename_zero(data)
        self.assertEqual(len(changes),2);self.assertEqual(len(data),len(result));self.assertEqual(result[:2],data[:2])
        out=struct.unpack_from('<'+'H'*len(words),result,2)
        self.assertEqual([v&511 for v in out[:4]],list(codes('Riko')))
        self.assertEqual([v&~511 for v in out],[v&~511 for v in words])
        self.assertEqual(rename_zero(result),(result,[]))
    def test_lowercase_zero_quantity_is_unchanged(self):
        data=struct.pack('<5H',2,*codes('zero'))
        self.assertEqual(rename_zero(data),(data,[]))
    def test_invalid_directory_is_refused(self):
        for data in (b'',b'\x03\x00xx',struct.pack('<4H',4,2,9,9),struct.pack('<2H',20,0)):
            with self.assertRaises(ValueError):message_ranges(data)

if __name__=='__main__':unittest.main()
