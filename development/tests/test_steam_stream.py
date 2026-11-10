import struct
import unittest
from pathlib import Path
from src.steam_stream import decode_sngw,encode_sngw,ogg_info,clear_records,native_title_info

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'work/steam_port_20261109/original/nativeDX10/X4/sound/bgm'

@unittest.skipUnless(BASE.exists(),'Local game backups required; never distributed with tests')
class StreamTests(unittest.TestCase):
    def test_native_roundtrip_and_duration(self):
        for suffix,name in [('', 'BGM5_0001'),('_eng','eng/BGM5_U_00000')]:
            raw=(BASE/('wav/clear/'+name+'.sngw')).read_bytes()
            plain=decode_sngw(raw)
            self.assertEqual(encode_sngw(plain,raw[:4]),raw)
            self.assertEqual(ogg_info(plain)['frames'],clear_records((BASE/('x4_clear'+suffix+'.stqr')).read_bytes())[0]['frames'])

    def test_damaged_stream_rejected(self):
        raw=(BASE/'wav/clear/BGM5_0001.sngw').read_bytes()
        bad=bytearray(raw);bad[len(bad)//2]^=1
        for value in (raw[:16],raw[:-1],bytes(bad),b'OggS'+raw[4:]):
            with self.subTest(length=len(value)):
                with self.assertRaises(ValueError):decode_sngw(value)

    def test_bad_bank_pointer_and_format_rejected(self):
        raw=(BASE/'x4_clear.stqr').read_bytes()
        for at,value in [(56,len(raw)),(72,44100),(8,4)]:
            bad=bytearray(raw);struct.pack_into('<I',bad,at,value)
            with self.subTest(offset=at):
                with self.assertRaises(ValueError):clear_records(bytes(bad))

    def test_playable_ogg_without_native_version_is_rejected(self):
        path=ROOT/'out/steam_title_voice_20261109_v1/nativeDX10/X4/sound/bgm/wav/clear/BGM5_0001.sngw'
        if not path.exists():self.skipTest('Failure reproduction fixture unavailable')
        raw=path.read_bytes()
        self.assertEqual(ogg_info(decode_sngw(raw))['rate'],48000)
        with self.assertRaisesRegex(ValueError,'native X4'):native_title_info(raw)

    def test_original_native_metadata(self):
        self.assertEqual(native_title_info((BASE/'wav/clear/BGM5_0001.sngw').read_bytes())['frames'],601598)

if __name__=='__main__':unittest.main()
