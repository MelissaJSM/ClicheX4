"""Compile indexed world-space HQ frames, sharing complete expression layers."""
import sys,json,struct,zlib
from pathlib import Path
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_ui_atlas import write_tile,aliased_composition,local_composition
from src.psx_static_effect import compose_static

def compile_mode(mode):
 d=H/mode;dictionary={};state_data=[];reports=[]
 for state in range(18):
  frames=[np.array(Image.open(d/'art'/f'{state:02}'/f'{n:02}.png')) for n in range(12)]
  patterns={};records=[];headers=[None]*12
  def tile_record(px,x,y):
   px=bytes(px)
   if px not in patterns:
    # Physical stage page boundaries: local base 768.
    free=next(t for t in range(176) if t not in patterns.values() and ((768+t)%16!=0 or not any(px[::16])) and ((768+t)%176>=16 or not any(px[:16])))
    patterns[px]=free
   return (0,patterns[px],x-80,y-80)
  def tiles(a):
   return {(x,y):a[y:y+16,x:x+16].tobytes()for y in range(16,144,16)for x in range(16,144,16)if a[y:y+16,x:x+16].any()}
  for group in [[0,1,2,11],[3,4,5],[6,7,8],[9],[10]]:
   ts=[tiles(frames[n])for n in group];same={xy:px for xy,px in ts[0].items()if all(t.get(xy)==px for t in ts)}
   start=len(records);records.extend(tile_record(px,*xy)for xy,px in same.items());prior={}
   for n,t in zip(group,ts):
    changed={xy:px for xy,px in t.items()if xy not in same}
    # Never silently cover an earlier opaque pixel with transparency.
    if any(any(a and not b for a,b in zip(px,changed.get(xy,bytes(256))))for xy,px in prior.items()):
     start=len(records);records.extend(tile_record(px,*xy)for xy,px in t.items());prior={};headers[n]=(start,len(records)-start)
    else:
     records.extend(tile_record(px,*xy)for xy,px in changed.items());prior.update(changed);headers[n]=(start,len(records)-start)
  bank=bytearray(48)
  for n,(start,count)in enumerate(headers):struct.pack_into('<HH',bank,n*4,count,12+start)
  for flags,t,x,y in records:bank.extend(struct.pack('<BBbb',flags,t,x,y))
  assert len(bank)<=1060,(mode,state,len(bank));bank=bytes(bank).ljust(1060,b'\0')
  atlas=bytearray(176*128);lut=[0xffff]*176
  for px,t in patterns.items():
   write_tile(atlas,t,px);packed=bytes(px[k]|px[k+1]<<4 for k in range(0,256,2))
   if packed not in dictionary:dictionary[packed]=len(dictionary)
   lut[t]=dictionary[packed]
  for n,a in enumerate(frames):
   p,sz,bb,_=compose_static(atlas,local_composition(aliased_composition(struct.pack('<I',4)+bank,0,n)))
   canvas=np.zeros_like(a);canvas[80+bb[1]:80+bb[3],80+bb[0]:80+bb[2]]=np.frombuffer(p,np.uint8).reshape(sz[1],sz[0]);assert np.array_equal(canvas,a),(state,n)
  state_data.append(struct.pack('<176H',*lut)+bank)
  reports.append({'state':state,'tiles':len(patterns),'records':len(records),'max_parts':max(c for _,c in headers),'bank_bytes_used':48+len(records)*4})
 out=d/'compiled';out.mkdir(exist_ok=True)
 ordered=sorted(dictionary);remap={dictionary[p]:n for n,p in enumerate(ordered)}
 state_data=[struct.pack('<176H',*(remap.get(t,0xffff)for t in struct.unpack('<176H',s[:352])))+s[352:]for s in state_data]
 raw=struct.pack('<4I',len(dictionary),176,1060,18)+b''.join(ordered)+b''.join(state_data)
 (out/'dictionary.bin').write_bytes(b''.join(ordered));(out/'states.bin').write_bytes(b''.join(state_data));(out/'raw.bin').write_bytes(raw)
 for n,data in enumerate(state_data):(out/f'state{n:02}.bin').write_bytes(data)
 result={'mode':mode,'unique_tiles':len(dictionary),'raw_bytes':len(raw),'zlib_estimate':len(zlib.compress(raw,9)),'states':reports,'all_216_frames_exact':True}
 (out/'report.json').write_text(json.dumps(result,indent=2));print(mode,result)
if __name__=='__main__':
 for mode in ['ver_rin_nana','ver_buki_riko']:compile_mode(mode)
