"""새 벽 동작의 정확 재추출, 전체 부분 조합, 총구 및 누적 자원 보존 검사."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,decode_stream,indexed_atlas
from src.psx_disc import file_hash
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
import prepare_wall_complete as maker
from review_wall_partial import targets,compose

EXPECTED='db508292c2746b5c4a12e60e9cf28f5ebe558e7998788c3d1d5440a4f8fd481a'

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed')
 sources=read_disc(SOURCE,('PL00_U.ARC','SLUS_005.61'))[0]
 out=H/'prepared_wall_front01';parent=H/'prepared_front_return01';old=(parent/'PL00_U.ARC').read_bytes();actual=(out/'PL00_U.ARC').read_bytes();need(sha(actual)==EXPECTED,'Prepared ARC changed')
 desired=targets();rebuilt,repro=maker.pack(old,desired);need(rebuilt==actual,'Reproduction differs')
 a=Archive(actual);p=Archive(old);original=Archive(sources['PL00_U.ARC']);parts=0;mask_checks=0;layer_checks=0
 for n in range(55,67):
  f=a.banks[0]['frames'][n];need(f['tile_count']==32,'32-tile allocation changed');raw=decode_stream(a.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
  for b in(0,5,6,7,8):
   need(np.array_equal(a.layer(n,b)[0],desired[n][b]),'Exact indexed target differs');layer_checks+=1
   for part in composition_frame(a.c,b,n)['parts']:
    t=part['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    need(t<32,'Tile exceeds allocation');need(t%16!=0 or not tile[:,0].any(),'GPU horizontal edge');need(not part['flip_y']or t//16%16!=0 or not tile[0].any(),'GPU vertical edge');parts+=1
  for mask in range(16):
   for arm in(1,2):
    need(a.composite(n,mask,arm)[0].tobytes()==compose(p,desired[n],mask,arm).tobytes(),'Partial mask/arm render differs');mask_checks+=1
 stable_checks=0
 for n in(*range(120,126),156,157,158):
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==p.composite(n,mask,arm)[0].tobytes(),'Frozen lowHP/front changed');stable_checks+=1
 ui=(out/'ST0E_U1.ARC').read_bytes();need(ui==(parent/'ST0E_U1.ARC').read_bytes()and sha(ui)==maker.SELECTION_SHA,'Frozen selection changed')
 barrel_checks=0
 guards=json.loads((H/'wall_barrel_guard01/guard.json').read_text('utf8'))
 for r in guards['rows']:
  n=r['shot_ref'];bb=tuple(q+160 for q in r['barrel_rectangle_world_exclusive']);want=original.composite(n,0)[0].crop(bb).tobytes()
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].crop(bb).tobytes()==want,'Native muzzle or barrel differs');barrel_checks+=1
 # The new firing arm is the sole change relative to its new body key.
 firing_nonarm_checks=0
 for n in range(56,67,2):
  edit=np.array(Image.open(H/f'wall_shots_registered03/{n:03}_arm_mask.png'))>0
  r=next(q for q in guards['rows']if q['shot_ref']==n);x0,y0,x1,y1=r['barrel_rectangle_world_exclusive'];edit[y0+160:y1+160,x0+160:x1+160]=True
  for b in(0,5,6,7,8):need(np.array_equal(a.layer(n,b)[0][~edit],a.layer(n-1,b)[0][~edit]),'New nonarm body differs');firing_nonarm_checks+=1
 rejected=[]
 def reject(name,fn):
  try:fn()
  except(ValueError,AssertionError,KeyError):rejected.append(name)
  else:raise AssertionError(name+' unexpectedly accepted')
 reject('original_baseline_not_frozen_parent',lambda:maker.pack(sources['PL00_U.ARC'],desired))
 reject('changed_parent',lambda:maker.pack(bytes([old[0]^1])+old[1:],desired))
 reject('truncated_parent',lambda:maker.pack(old[:-1],desired))
 reject('missing_ref',lambda:maker.pack(old,{n:v for n,v in desired.items()if n!=55}))
 reject('extra_ref',lambda:maker.pack(old,{**desired,67:desired[55]}))
 for label,change in [('invalid_index',lambda v:v.__setitem__((160,160),16)),('outside_staging',lambda v:v.__setitem__((0,0),1))]:
  bad={n:{b:v.copy()for b,v in layers.items()}for n,layers in desired.items()};change(bad[55][0]);reject(label,lambda:maker.pack(old,bad))
 for label,v in [('wrong_shape',np.zeros((16,16),np.uint8)),('wrong_dtype',np.zeros((384,384),np.int16))]:
  bad={n:{b:q.copy()for b,q in layers.items()}for n,layers in desired.items()};bad[55][0]=v;reject(label,lambda:maker.pack(old,bad))
 # All six animation step tables are read from the actual immutable EXE.
 inventory=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'));exe=sources['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0];seq=[];step_checks=0
 def panel(n):
  board=Image.new('RGB',(4*256,340),'#1a202b');dr=ImageDraw.Draw(board)
  for col,(label,arc,mask)in enumerate((('base parent',p,0),('base new',a,0),('Fourth parent',p,15),('Fourth new',a,15))):
   im=arc.composite(n,mask)[0].crop((128,120,192,200)).resize((256,320),Image.Resampling.NEAREST);board.paste(im,(col*256,20),im);dr.text((col*256+4,4),f'{label} ref{n}',fill='white')
  return board
 for r in inventory['animations']:
  if r['id']not in(13,14,15,125,126,127):continue
  for s in r['steps']:
   off=0x800+int(s['address'],16)-load;need(exe[off:off+4].hex()==s['bytes'],'Actual executable animation step differs');step_checks+=1
  sequence=[panel(s['frame'])for s in r['steps']];durations=[round(s['duration_calls_uninterrupted']*1000/60)for s in r['steps']]
  for slowdown in(1,4):sequence[0].save(out/f'animation{r["id"]:03}_{slowdown}x.webp',save_all=True,append_images=sequence[1:],duration=[d*slowdown for d in durations],loop=0,lossless=True)
  seq.append({k:r[k]for k in('id','graphics_bank','composition_bank','loop_to_position','steps')})
 write(out/'sequences.json',{'kind':'native_step_order_review_simulation_not_gameplay','source_executable_sha256':sha(exe),'verified_actual_step_records':step_checks,'animations':seq,'display_calls_per_second_assumption':60,'loop_policy':'검토 영상은 표의 도달 스텝을 한 번씩 표시하고 재시작한다. 말단 유지·물리 이벤트·벽 충돌은 실제 게임 시뮬레이션이 아니다.','events_not_executed':True,'physics_not_simulated':True,'slowdown_copy':4})
 # Previous 55/56 preview was already viewed; require that revision02 is exact.
 preview_proof={}
 for n in(55,56):
  oldpreview=H/f'wall_partial_preview01/{n:03}.png';newpreview=H/f'wall_partial_preview02/{n:03}.png'
  if oldpreview.exists():need(Image.open(oldpreview).tobytes()==Image.open(newpreview).tobytes(),'First two partial previews changed');preview_proof[str(n)]=True
 proof={'passed':True,'source_bin_sha256':SOURCE_SHA,'parent_arc_sha256':sha(old),'reproduced_arc_sha256':sha(actual),'selection_sha256':sha(ui),'indexed_targets':layer_checks,'native_gpu_part_boundary_checks':parts,'partial_mask_arm_checks':mask_checks,'exact_original_barrel_mask_arm_checks':barrel_checks,'frozen_lowHP_front_mask_arm_checks':stable_checks,'new_body_outside_firing_arm_layer_checks':firing_nonarm_checks,'actual_executable_animation_step_checks':step_checks,'decoded_references':repro['decoded_references'],'nonselected_composites':repro['nonselected_composites'],'preserved_part_records':repro['preserved_part_records'],'rejected_inputs':rejected,'first_partial_preview_revisions_equal':preview_proof,'source_bin_unchanged_after':file_hash(SOURCE)==SOURCE_SHA,'zero_game_or_save_writes':True,'runtime_emulator_test':False,'complete_art_unification':False}
 write(out/'repro_and_rejections.json',proof);print(json.dumps(proof))

if __name__=='__main__':main()
