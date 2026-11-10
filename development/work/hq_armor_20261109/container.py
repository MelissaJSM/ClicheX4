"""Lossless chunked native-LZ container; original ARC size remains fixed."""
import sys,struct,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_compress import encode_stream
from src.psx_player import decode_stream

def make(mode):
 d=H/mode;c=d/'compiled';dictionary=(c/'dictionary.bin').read_bytes();states=(c/'states.bin').read_bytes()
 # Cache expensive deterministic native compression by exact uncompressed SHA.
 cache=H/'lzcache';cache.mkdir(exist_ok=True)
 def enc(raw):
  path=cache/(hashlib.sha256(raw).hexdigest()+'.bin')
  if path.exists():data=path.read_bytes()
  else:data=encode_stream(raw);path.write_bytes(data)
  assert decode_stream(data,0,len(data),len(raw)).data==raw
  return data
 # Directory: common-state stream, dictionary chunks (256 tiles max), static tail.
 chunks=[(0,0,states)]
 chunks += [(1,start//128,dictionary[start:start+32768])for start in range(0,len(dictionary),32768)]
 static=(d/'packing/non_x_texture.bin').read_bytes();keep=256*128
 chunks += [(2,start//128,static[start:start+32768])for start in range(keep,len(static),32768)]
 header=bytearray(struct.pack('<4I',0x52415148,len(chunks),len(dictionary)//128,0))
 directory=bytearray(16*len(chunks));payload=bytearray();details=[]
 for k,(kind,start,raw) in enumerate(chunks):
  data=enc(raw);offset=16+len(directory)+len(payload)
  struct.pack_into('<4I',directory,k*16,kind,start,offset,len(raw));payload.extend(data)
  if len(payload)%4:payload.extend(bytes(4-len(payload)%4))
  details.append({'kind':kind,'first_tile':start,'offset':offset,'raw':len(raw),'packed':len(data)})
 blob=bytes(header+directory+payload)
 capacity=120832-keep+2048-96
 print('SIZE',mode,len(blob),capacity,details,flush=True)
 assert len(blob)<=capacity,(len(blob),capacity)
 (c/'container.bin').write_bytes(blob)
 report={'mode':mode,'keep_static_tiles':keep//128,'remaining_static_tiles':(len(static)-keep)//128,'bytes':len(blob),'capacity':capacity,'chunks':details}
 (c/'container.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
if __name__=='__main__':
 for mode in ['ver_rin_nana','ver_buki_riko']:make(mode)
