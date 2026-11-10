"""패킹 재현, 총구/팔 경계, GPU 경계 및 부분표시 회귀 검사. 실기 아님."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from native_pose_pack import SOURCE,SOURCE_SHA,sha,load,packing,write
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_disc import file_hash
from src.psx_player import composition_frame,decode_stream,indexed_atlas
def main():
 raw=read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'];before={};after={};folder=H/'prepared_run_complete03'
 for n in range(3,33):
  f=H/('run_registered02'if n%2 else'shot_registered05');before[n]=load(f/'before'/f'{n:03}_indices.png');after[n]=load(f/'after'/f'{n:03}_indices.png')
 result,proof=packing(raw,before,after);expected=(folder/'PL02_U.ARC').read_bytes();assert result==expected
 a=Archive(result);old=Archive(raw);gpu=combos=muzzles=0
 for n in range(3,33):
  f=a.banks[0]['frames'][n];assert f['tile_count']==32
  decoded=decode_stream(a.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(decoded,32)[0],np.uint8).reshape(32,256)
  for b in(0,5,6,7,8):
   for q in composition_frame(a.c,b,n)['parts']:
    t=q['tile'];p=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    assert t%16!=0 or not p[:,0].any();assert not(q['flip_y'] and t//16%16==0 and p[0].any());gpu+=1
  for mask in range(16):
   im=np.array(a.composite(n,mask)[0]);want=np.array(a.rgba(before[n],16)if mask&1 else a.rgba(after[n],0))
   for flip in(False,True):assert np.array_equal(im[:,::-1]if flip else im,want[:,::-1]if flip else want);combos+=1
  if not n%2:
   for kind,mask in [('before',15),('after',0)]:
    barrel=np.array(Image.open(H/f'shot_inputs01/before/{n:03}_barrel_indices.png'));v=np.array(a.composite(n,mask)[0]);want=np.array(old.composite(n,mask)[0]);m=barrel>0
    assert np.array_equal(v[m],want[m]);muzzles+=1
 tests=[('wrong_source',lambda:packing(raw[:-1]+bytes([raw[-1]^1]),before,after)),('missing_after',lambda:packing(raw,before,{n:v for n,v in after.items()if n!=3})),('accepted_idle',lambda:packing(raw,{0:before[3]},{0:after[3]})),('wrong_canvas',lambda:packing(raw,{3:before[3][:-1]},{3:after[3]})),('wrong_scope',lambda:packing(raw,{120:before[3]},{120:after[3]}))]
 bad={n:v.copy()for n,v in after.items()};bad[3][150,120]=5;tests.append(('after_outside_coat',lambda:packing(raw,before,bad)))
 wrong_palette={n:v.copy()for n,v in before.items()};wrong_palette[3][150,150]=16;tests.append(('out_of_palette_index',lambda:packing(raw,wrong_palette,after)))
 tests.append(('wrong_index_dtype',lambda:packing(raw,{3:before[3].astype(np.float32)},{3:after[3]})))
 rejects=[]
 for name,fn in tests:
  try:fn()
  except ValueError as e:rejects.append({'case':name,'rejected':True,'reason':str(e)})
  else:raise AssertionError(name)
 assert file_hash(SOURCE)==SOURCE_SHA
 report={'passed':True,'reproduced_sha256':sha(result),'byte_identical':True,'source_bin_preserved':True,'gpu_parts_checked':gpu,'mask_direction_combinations':combos,'native_barrel_comparisons':muzzles,'native_barrel_rgba_original_exact':True,'rejections':rejects,'actual_arc_sheets_viewed':[f'{kind}/actual_{i:02}.png'for kind in('before','after')for i in range(4)],'runtime_verified':False,'production_scope':'Ultimate 이동/사격32참조 중 수용1/2보존·3..32양폼교정. 다른 동작은 이후 작업.'}
 write(folder/'repro_and_rejections.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
