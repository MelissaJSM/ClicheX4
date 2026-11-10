import struct
import unittest
from src.psx_korean_text import build_dialogue,glyph_bitmap,replace_text_same_capacity
from src.psx_korean_font import font_cache_proposal
from scripts.inventory_korean import messages
from scripts.discover_inputs import psx_arc
from scripts.verify_korean_dialogue import verify_typewriter

class KoreanTextTests(unittest.TestCase):
    def source(self):
        # One instant speaker line and one typed body, ending the message.
        words=(0x404a,0x104b,0x91ff)
        return struct.pack('<4H',2,*words)

    def test_directory_flags_and_space(self):
        source=self.source();new,r=build_dialogue(source,messages(source),{0:[['리코','가 나']]})
        start=struct.unpack_from('<H',new)[0];words=struct.unpack_from('<5H',new,start)
        self.assertEqual(start,144);self.assertEqual(new[128:132],b'KOR1')
        self.assertEqual(words[0]&0xf800,0)
        self.assertEqual(words[1]&0xf800,0x4000)
        self.assertEqual(words[2]&0xf800,0x1000)
        self.assertEqual(words[3],0x17ff)
        self.assertEqual(words[4]&0xf800,0x9000)
        self.assertEqual(r['translated_pages'],1)
        self.assertEqual(new[r['font_offset']:r['font_offset']+18],glyph_bitmap(r['glyphs'][0]))

    def test_refuses_page_and_width_overflow(self):
        source=self.source();mm=messages(source)
        for translation in ({0:[]},{0:[['가'*21]]},{0:[['가','나','다','라']]}):
            with self.assertRaises(ValueError):build_dialogue(source,mm,translation)

    def test_single_glyph_x_header_expands_instantly_but_body_stays_typed(self):
        # X's one native glyph also has the header-final yield bit. It must
        # not turn every character of the translated full name into body.
        for side in (0,0x800):
            original=[[0x5061|side],[0x104a|side,0xa04b|side]]
            source=struct.pack('<4H',2,*original[0],*original[1])
            out,_=build_dialogue(source,messages(source),{0:[['텐코 시부키','가나']]},
                                 immediate_headers={(0,0)})
            words=list(struct.unpack_from('<8H',out,144))
            self.assertTrue(all(w&0x1000==0 for w in words[:5]))
            self.assertEqual(words[5]&0xf800,side|0x5000)
            self.assertEqual(words[6]&0xf800,side|0x1000)
            self.assertEqual(words[7]&0xf800,side|0xa000)
            check=verify_typewriter(original,[words[:6],words[6:]],speaker_header=True)
            self.assertTrue(check['immediate_header'] and check['body_typewriter'])

    def test_explicit_header_requires_existing_page_and_newline(self):
        source=struct.pack('<3H',2,0x104a,0x804b)
        for pages in ({(0,1)},{(0,0)}):
            with self.assertRaises(ValueError):
                build_dialogue(source,messages(source),{0:[['가나']]},immediate_headers=pages)

    def test_rejects_unknown_executable(self):
        with self.assertRaises(ValueError):font_cache_proposal(bytes(4096))

    def test_terminal_without_typewriter_does_not_make_body_instant(self):
        # Actual US profile: an instant header may yield on its last glyph,
        # body glyphs yield individually, final glyph only ends the page.
        for side in (0,0x800):
            for ending in (0x2000,0xa000,0x3000,0xb000):
                for header_yield in (0,0x1000):
                    with self.subTest(side=side,ending=ending,header_yield=header_yield):
                        old=[0x4a|side,0x404b|side|header_yield,
                             0x104c|side,0x504d|side,0x104e|side,0x4f|side|ending]
                        source=struct.pack('<'+'H'*(len(old)+1),2,*old)
                        new,_=build_dialogue(source,messages(source),{0:[['리코','가 나','다라']]})
                        start=struct.unpack_from('<H',new)[0]
                        words=list(struct.unpack_from('<7H',new,start))
                        self.assertEqual([w&0xf800 for w in words],
                                         [side,side|0x4000|header_yield,
                                          side|0x1000,side|0x1000,side|0x5000,
                                          side|0x1000,side|ending])
                        profile=verify_typewriter([old[:2],old[2:4],old[4:]],
                                                  [words[:2],words[2:5],words[5:]])
                        self.assertTrue(profile['body_typewriter'])

    def test_no_header_body_retains_timing_and_native_first_yield(self):
        old=[0x104a,0x104b,0x804c]
        source=struct.pack('<4H',2,*old)
        new,_=build_dialogue(source,messages(source),{0:[['가나다']]})
        words=list(struct.unpack_from('<3H',new,144))
        self.assertEqual([w&0xf800 for w in words],[0x1000,0x1000,0x8000])
        # Native func_8002328C loops only while (word & 0xB000)==0.
        emitted=0
        for word in words:
            emitted+=1
            if word&0xb000:break
        self.assertEqual(emitted,1)
        self.assertTrue(verify_typewriter([old],[words])['body_typewriter'])

    def test_independent_timing_verifier_rejects_previous_generator_bug(self):
        original=[[0x4a,0x504b],[0x104c,0xa04d]]
        with self.assertRaisesRegex(ValueError,'Body typewriter'):
            verify_typewriter(original,[[0x100,0x4101],[0x102,0xa103]])
        with self.assertRaisesRegex(ValueError,'speaker final'):
            verify_typewriter(original,[[0x100,0x4101],[0x1102,0xa103]])
        with self.assertRaisesRegex(ValueError,'Page-final'):
            verify_typewriter(original,[[0x100,0x5101],[0x1102,0xb103]])

    def test_mixed_body_timing_is_not_silently_flattened(self):
        source=struct.pack('<4H',2,0x104a,0x004b,0x804c)
        with self.assertRaisesRegex(ValueError,'Mixed body'):
            build_dialogue(source,messages(source),{0:[['가나다']]})

    def archive(self,entries):
        header=bytearray(2048);payload=bytearray()
        for i,(kind,data) in enumerate(entries):
            struct.pack_into('<II',header,8+i*8,kind,len(data))
            payload+=data+bytes((-len(data))%2048)
        struct.pack_into('<II',header,0,len(entries),2048+len(payload))
        return bytes(header+payload)

    def test_grown_text_keeps_next_archive_word_aligned(self):
        original=self.archive([(9,b'KEEP'),(0x15,bytes(16))])
        for length in (17,18,19,20,2048):
            with self.subTest(length=length):
                text=bytes([0x5a])*length
                patched=replace_text_same_capacity(original,text)
                entries=psx_arc(patched);last=entries[-1]
                self.assertEqual(len(patched),len(original))
                self.assertEqual(last['size'],(length+3)&~3)
                # This models the native loader's unrounded RAM cursor.
                ram_cursor=0x80170000+sum(e['size'] for e in entries)
                self.assertEqual(ram_cursor%4,0)
                self.assertEqual(patched[last['offset']:last['offset']+length],text)
                self.assertEqual(patched[last['offset']+length:last['offset']+last['size']],bytes(last['size']-length))
                self.assertEqual(patched[2048:4096],original[2048:4096])

    def test_shorter_text_preserves_declared_allocation(self):
        original=self.archive([(0x15,bytes(24))])
        patched=replace_text_same_capacity(original,b'short')
        self.assertEqual(psx_arc(patched)[0]['size'],24)

    def test_rejects_unaligned_ram_resource_and_overflow(self):
        unaligned=self.archive([(9,b'xx'),(0x15,bytes(16))])
        with self.assertRaisesRegex(ValueError,'Unaligned'):
            replace_text_same_capacity(unaligned,b'abcd')
        original=self.archive([(0x15,bytes(16))])
        with self.assertRaisesRegex(ValueError,'allocation'):
            replace_text_same_capacity(original,bytes(2049))

if __name__=='__main__':unittest.main()
