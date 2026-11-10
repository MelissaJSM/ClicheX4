import struct,unittest
from src.psx_shibuki_text import char,code,rename_shibuki
from src.psx_text import message_ranges
from src.psx_ui_text_space import compact_parts,expand_dialogue_from_parts
from src.psx_ui_atlas import aliased_composition
from scripts.discover_inputs import psx_arc

def textdata(lines):
    words=[]
    for line in lines:
        w=[code(c)|0x1000 for c in line];w[-1]|=0x4000;words+=w
    words[-1]=(words[-1]&~0x4000)|0x8000
    return struct.pack('<H',2)+struct.pack('<'+'H'*len(words),*words)

def partsfixture():
    records=[bytes((0,1,255,2)),bytes((64,2,4,250)),bytes((128,3,8,9))]
    bank=struct.pack('<III',3<<16|2,5<<16|2,7<<16|2)+records[0]+records[1]+records[1]+records[2]+records[0]+records[1]
    return struct.pack('<II',8,8+len(bank))+bank+bank+bytes(4096)

def arcfixture(parts,text):
    blocks=[(3,parts),(0x123,b'PROTECTED'),(0x15,text)];out=bytearray(2048)
    for i,(kind,data) in enumerate(blocks):
        struct.pack_into('<II',out,8+8*i,kind,len(data));out+=data+bytes((-len(data))%2048)
    struct.pack_into('<II',out,0,len(blocks),len(out));return bytes(out)

class ShibukiTextTest(unittest.TestCase):
    def test_character_names_and_idempotence(self):
        for name in ('X','Megaman','MEGAMAN','Mega Man X'):
            data=textdata([name,'Good luck'])
            out,report=rename_shibuki(data);self.assertEqual(report['name_count'],1)
            words=struct.unpack_from('<'+'H'*((len(out)-2)//2),out,2)
            self.assertEqual(''.join(map(char,words[:7])),'Shibuki')
            self.assertEqual(words[6]&0x4000,0x4000)
            self.assertTrue(all(w&0x1000 for w in words));self.assertEqual(words[-1]&0xa000,0x8000)
            self.assertEqual(rename_shibuki(out)[0],out);self.assertEqual(rename_shibuki(out)[1]['name_count'],0)

    def test_unrelated_words_and_bytes_stay_exact(self):
        data=textdata(['EXTRA MAX X4','small x Megamania'])
        out,report=rename_shibuki(data);self.assertEqual(out,data);self.assertEqual(report['changes'],[])

    def test_overflow_wrap_preserves_page_and_speaker(self):
        data=textdata(['Iris','Please be careful X'])
        out,report=rename_shibuki(data);self.assertEqual(report['pages'],1)
        words=struct.unpack_from('<'+'H'*((len(out)-2)//2),out,2)
        lines=[];s=''
        for w in words:
            s+=char(w)
            if w&0xe000:lines.append(s);s=''
        self.assertEqual(lines[0],'Iris');self.assertTrue(all(len(v)<=20 for v in lines))
        self.assertIn('Shibuki',' '.join(lines));self.assertEqual(len(message_ranges(out)),1)

    def test_unreviewed_page_overflow_is_refused(self):
        data=textdata(['Iris','X abcdefghijklmnopqrs abcdefghijklmnopqrs abcdefghijklmnopqrs'])
        with self.assertRaises(ValueError):rename_shibuki(data)

    def test_invalid_text_directory_is_refused(self):
        for data in (b'',b'\x03\x00xxxx',struct.pack('<4H',4,2,0,0)):
            with self.assertRaises(ValueError):rename_shibuki(data)

class UIPartsSpaceTest(unittest.TestCase):
    def test_lossless_record_order_flips_coordinates_and_determinism(self):
        parts=partsfixture();out,proof=compact_parts(parts)
        self.assertEqual(len(out),len(parts)-2048);self.assertEqual(proof['checked_composition_frames'],6)
        for b in range(2):
            for n in range(3):
                before=aliased_composition(parts,b,n);after=aliased_composition(out,b,n)
                clean=lambda c:[{k:v for k,v in p.items() if k!='record_offset'} for p in c['parts']]
                self.assertEqual(clean(before),clean(after))
        self.assertEqual(compact_parts(parts),(out,proof))

    def test_capacity_and_corruption_refused(self):
        parts=partsfixture()
        with self.assertRaises(ValueError):compact_parts(parts,8192)
        bad=bytearray(parts);struct.pack_into('<I',bad,12,0xffff0002)
        with self.assertRaises(ValueError):compact_parts(bad)

    def test_fixed_size_archive_preserves_other_entries(self):
        parts=partsfixture();original=arcfixture(parts,b'abc');out,proof=expand_dialogue_from_parts(original,b'A'*2200)
        self.assertEqual(len(out),len(original));self.assertTrue(proof['graphics_bytes_preserved'])
        entries=psx_arc(out)
        self.assertEqual(out[entries[1]['offset']:entries[1]['offset']+9],b'PROTECTED')
        self.assertEqual(out[entries[-1]['offset']:entries[-1]['offset']+2200],b'A'*2200)
        for replacement in (b'AB',b'A'*5000):
            with self.assertRaises(ValueError):expand_dialogue_from_parts(original,replacement)

if __name__=='__main__':unittest.main()
