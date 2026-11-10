import struct,unittest
from scripts.prepare_shibuki_weapon_palette import edited_palette,WEAPON_ROWS,FLASHES
class WeaponPaletteTests(unittest.TestCase):
 def sample(self):return b''.join(struct.pack('<16H',0,*[0x8000|((i+row)%31+1) for i in range(15)]) for row in range(77))
 def test_selected_body_rows_only(self):
  old=self.sample();new,rows=edited_palette(old)
  for row in range(77):
   if row not in WEAPON_ROWS and row not in FLASHES:self.assertEqual(old[row*32:row*32+32],new[row*32:row*32+32])
   self.assertEqual(new[row*32:row*32+2],b'\0\0')
  for row in WEAPON_ROWS:self.assertEqual(new[row*32:row*32+32],old[:32])
  self.assertEqual(len(rows),15)
 def test_wrong_size_and_transparency_rejected(self):
  with self.assertRaises(ValueError):edited_palette(bytes(32))
  old=bytearray(self.sample());old[3*32]=1
  with self.assertRaises(ValueError):edited_palette(old)
 def test_original_high_bits_preserved(self):
  old=bytearray(self.sample());struct.pack_into('<H',old,38*32+2,17);new,_=edited_palette(old)
  self.assertFalse(struct.unpack_from('<H',new,38*32+2)[0]&0x8000)
if __name__=='__main__':unittest.main()
