import struct,unittest
from src.steam_audio import wave_info,mute_wave,sequence_events

def fixture():
 fmt=struct.pack('<HHIIHHHHH',2,1,48000,26250,70,4,32,128,7)
 fmt+=b''.join(struct.pack('<hh',a,b) for a,b in ((256,0),(512,-256),(0,0),(192,64),(240,0),(460,-208),(392,-232)))
 content=b'WAVEfmt '+struct.pack('<I',50)+fmt+b'data'+struct.pack('<I',70)+b'\x00\x10\x00'+bytes(67)
 return b'RIFF'+struct.pack('<I',len(content))+content

class AudioValidation(unittest.TestCase):
 def test_truncated_chunk_and_false_riff_length_rejected(self):
  b=fixture()
  for bad in (b[:3],b[:-1],b[:4]+struct.pack('<I',len(b))+b[8:]):
   with self.assertRaises(ValueError):wave_info(bad)
 def test_non_native_block_rejected(self):
  b=bytearray(fixture());struct.pack_into('<H',b,32,128);struct.pack_into('<H',b,38,244)
  with self.assertRaises(ValueError):wave_info(b)
 def test_native_authoring_trailer_preserved_by_mute(self):
  tail=b'tIME'+struct.pack('<I',8)+b'12345678'+b'ver.'+struct.pack('<II',4,1)
  b=fixture()+tail;new=mute_wave(b)
  self.assertEqual(new[-28:],tail);self.assertEqual(wave_info(new),wave_info(b))
  with self.assertRaises(ValueError):wave_info(b[:-1]+b'XX')
 def test_event_table_outside_file_rejected(self):
  b=bytearray(52);b[:8]=b'SRQR\x05\0\0\0';struct.pack_into('<I',b,8,14);struct.pack_into('<I',b,32,1900)
  with self.assertRaises(ValueError):sequence_events(b)
