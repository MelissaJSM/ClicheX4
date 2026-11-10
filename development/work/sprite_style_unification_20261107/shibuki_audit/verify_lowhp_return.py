"""새 저체력+귀환 준비본 재현, 거부, 파츠경계, 연속재생 자료 검사."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from src.psx_player import indexed_atlas,decode_stream,composition_frame
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from prepare_lowhp_final import make_targets,compose
import prepare_lowhp_final as native_inputs
from pack_lowhp_return import pack

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');baseline=read_disc(SOURCE,('PL00_U.ARC','SLUS_005.61'))[0]
 parent=(H/'prepared_return158_01/PL00_U.ARC').read_bytes();old=Archive(baseline['PL00_U.ARC']);desired,_,_,_=make_targets(old)
 out=H/'prepared_lowhp_return01';actual=(out/'PL00_U.ARC').read_bytes();rebuilt,proof=pack(parent,desired);need(rebuilt==actual,'Rebuild differs')
 a=Archive(actual);ret=Archive(parent);parts=0
 for n in(*range(120,126),158):
  f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
  need(f['tile_count']<=32,'32tile limit')
  for b in(0,5,6,7,8):
   for p in composition_frame(a.c,b,n)['parts']:
    t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    need(t%16!=0 or not tile[:,0].any(),'GPU horizontal edge');need(not p['flip_y']or t//16%16!=0 or not tile[0].any(),'GPU vertical edge');parts+=1
 counts=0;footchecks=0
 for n in range(120,126):
  for mask in range(16):
   for arm in(1,2):
    want=compose(old,desired[n],mask,arm);got=a.composite(n,mask,arm)[0];need(want.tobytes()==got.tobytes(),'Native target mismatch');counts+=1
    reference=np.array(a.composite(120,mask,arm)[0]);need(np.array_equal(np.array(got)[178:],reference[178:]),'Sole contact changes');footchecks+=1
  for b in(0,5,6,7,8):need(np.array_equal(a.layer(n,b)[0],desired[n][b]),'Layer target mismatch')
 for mask in range(16):
  for arm in(1,2):need(a.composite(158,mask,arm)[0].tobytes()==ret.composite(158,mask,arm)[0].tobytes(),'Frozen return changed')
 rejected=[]
 invalid={n:{b:v.copy()for b,v in layers.items()}for n,layers in desired.items()};invalid[120][0][160,160]=16
 missing={n:v for n,v in desired.items()if n!=125}
 shape={n:{b:v.copy()for b,v in layers.items()}for n,layers in desired.items()};shape[120][0]=np.zeros((32,32),np.uint8)
 for name,fn in [('wrong_parent',lambda:pack(baseline['PL00_U.ARC'],desired)),('changed_parent',lambda:pack(bytes([parent[0]^1])+parent[1:],desired)),('truncated_parent',lambda:pack(parent[:-1],desired)),('missing_ref',lambda:pack(parent,missing)),('invalid_index',lambda:pack(parent,invalid)),('invalid_shape',lambda:pack(parent,shape))]:
  try:fn()
  except ValueError:rejected.append(name)
  else:raise AssertionError(name+' accepted')
 key=next(iter(native_inputs.NATIVE_INPUT_SHA));saved_hash=native_inputs.NATIVE_INPUT_SHA[key]
 try:
  native_inputs.NATIVE_INPUT_SHA[key]='0'*64
  try:make_targets(old)
  except ValueError:rejected.append('registered_native_hash_mismatch')
  else:raise AssertionError('bad native hash accepted')
 finally:native_inputs.NATIVE_INPUT_SHA[key]=saved_hash
 animation=animation_map(baseline['SLUS_005.61'])[0][6];steps=animation['steps'];need(set(q['frame']for q in steps)==set(range(120,126)),'Native lowHP table changed')
 def panel(n):
  board=Image.new('RGB',(4*240,288+30),'#1a202b');dr=ImageDraw.Draw(board)
  for i,(label,arc,mask)in enumerate((('base current',old,0),('base new',a,0),('Fourth current',old,15),('Fourth new',a,15))):
   p=arc.composite(n,mask)[0].crop((136,132,184,188)).resize((240,280),Image.Resampling.NEAREST);board.paste(p,(i*240,30),p);dr.text((i*240+4,6),f'{label} / {n}',fill='white')
  return board
 frames=[panel(0)];dur=[700];calls=[]
 for row in steps:
  ticks=row['duration_ticks'];tick=ticks if ticks>0 else 256 if ticks==0 else 255;frames.append(panel(row['frame']));dur.append(round(tick*1000/60));calls.append(tick)
 frames[0].save(out/'sequence.webp',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True)
 frames[0].save(out/'sequence_4x.webp',save_all=True,append_images=frames[1:],duration=[700]+[v*4 for v in dur[1:]],loop=0,lossless=True)
 write(out/'sequence.json',{'kind':'native_animation_table_frame_simulation_not_gameplay','source_exe_sha256':sha(baseline['SLUS_005.61']),'animation':animation,'native_calls':calls,'timer_calls_per_second_assumption':60,'extra_idle_hold':True,'four_times_slow_copy':True,'not_actual_runtime':True})
 write(out/'repro_and_rejections.json',{'passed':True,'source_bin_sha256':SOURCE_SHA,'reproduced_PL00_sha256':sha(actual),'GPU_boundary_parts':parts,'native_targets_all_mask_arm':counts,'feet_178_plus_checks':footchecks,'frozen_return158_mask_arm_checks':32,'rejected_inputs':rejected,'original_idle0_115_119_and_other_frames_preserved':True,'source_bin_unchanged_after':file_hash(SOURCE)==SOURCE_SHA,'runtime_emulator_test':False,'whole_style_unification_complete':False})
 print(json.dumps({'passed':True,'sha256':sha(actual),'parts':parts,'native_targets':counts,'rejects':len(rejected),'animation6':animation,'calls':calls}))
if __name__=='__main__':main()

