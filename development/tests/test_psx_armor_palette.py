import struct,unittest
from src.psx_armor_palette import replace_armor_palette_rows

class ArmorPaletteTests(unittest.TestCase):
    def test_weapon_effect_row_is_skipped(self):
        old=b''.join(struct.pack('<16H',0,*[r*16+i+1 for i in range(15)]) for r in range(11))
        colors=[0]+[0x8000|i*33 for i in range(1,16)]
        new,rows=replace_armor_palette_rows(old,colors,[0],{},weapon_rows=[3,7])
        self.assertEqual(rows,[1,2,5,6,9,10])
        for r in (0,3,4,7,8):self.assertEqual(new[r*32:r*32+32],old[r*32:r*32+32])
        with self.assertRaises(ValueError):replace_armor_palette_rows(old,colors,[0],{},weapon_rows=[1])
        with self.assertRaises(ValueError):replace_armor_palette_rows(old,colors,[0],{},weapon_rows=[0])
    def test_only_selected_armor_rows_and_bit15_preserved(self):
        old=b''.join(struct.pack('<16H',0,*[(r*16+i+1)|(0x8000 if i%2 else 0) for i in range(15)]) for r in range(12))
        colors=[0]+[0x8000|i*1024|i*32|i for i in range(1,16)]
        new,rows=replace_armor_palette_rows(old,colors,[0,3,9],{9:((31,31,31),.5)})
        self.assertEqual(rows,[1,2,4,5,10,11]);self.assertEqual(len(old),len(new))
        for r in range(12):
            a=struct.unpack_from('<16H',old,r*32);b=struct.unpack_from('<16H',new,r*32)
            if r not in rows:self.assertEqual(a,b)
            else:
                self.assertEqual(b[0],0)
                self.assertEqual([x&0x8000 for x in a],[x&0x8000 for x in b])
        self.assertEqual(struct.unpack_from('<H',new,32+2)[0]&0x7fff,colors[1]&0x7fff)
        self.assertGreater(struct.unpack_from('<H',new,10*32+2)[0]&31,colors[1]&31)

    def test_bad_ranges_and_transparency_rejected(self):
        old=struct.pack('<16H',0,*range(1,16))*8;colors=[0]+list(range(1,16))
        for rows in ([0,0],[0,1],[7],[-1]):
            with self.assertRaises(ValueError):replace_armor_palette_rows(old,colors,rows,{})
        for data in (old+b'X',old[:32]+b'XX'+old[34:]):
            with self.assertRaises(ValueError):replace_armor_palette_rows(data,colors,[0],{})
        with self.assertRaises(ValueError):replace_armor_palette_rows(old,[1]+colors[1:],[0],{})
        with self.assertRaises(ValueError):replace_armor_palette_rows(old,colors,[0],{3:((31,31,31),.5)})

if __name__=='__main__':unittest.main()
