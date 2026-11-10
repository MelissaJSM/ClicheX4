"""새 귀환/선택 준비본의 재현, 잘못된 입력, GPU 경계, 시퀀스 검증."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import indexed_atlas,decode_stream,composition_frame
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_disc import file_hash
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
import prepare_front_return as maker
from sync_front_return_ui import patch

def world_ui(ui,n):
 cp=aliased_composition(entry(ui,10),2,n);px,size,bb,_=compose_static(entry(ui,0x10102)[90112:],local_composition(cp));v=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);y,x=np.nonzero(v)
 out=np.zeros((384,384),np.uint8);out[y+bb[1]+160,x+bb[0]+160]=v[y,x];return out

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed')
 sources=read_disc(SOURCE,('PL00_U.ARC','COL0E_U1.ARC','SLUS_005.61'))[0];original=Archive(sources['PL00_U.ARC']);out=H/'prepared_front_return01';parent=H/'prepared_lowhp_return01'
 old=(parent/'PL00_U.ARC').read_bytes();oldui=(parent/'ST0E_U1.ARC').read_bytes();pal=entry(sources['COL0E_U1.ARC'],5)
 desired,owner,ring,_=maker.targets(original);rebuilt,proof=maker.pack(old,desired);actual=(out/'PL00_U.ARC').read_bytes();need(actual==rebuilt,'Gameplay reproducibility differs')
 ui,uiinfo,_,_=patch(old,actual,oldui,pal);need(ui==(out/'ST0E_U1.ARC').read_bytes(),'Selection reproducibility differs')
 a=Archive(actual);stable=Archive(old);parts=0
 for n in(156,157,158):
  f=a.banks[0]['frames'][n];need(f['tile_count']<=32,'Native tile budget exceeded');raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
  for b in(0,5,6,7,8):
   for p in composition_frame(a.c,b,n)['parts']:
    t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    need(t%16!=0 or not tile[:,0].any(),'Player horizontal GPU edge');need(not p['flip_y']or t//16%16!=0 or not tile[0].any(),'Player vertical GPU edge');parts+=1
 counts=0
 for n in(156,157,158):
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==maker.compose(original,desired[n],mask,arm).tobytes(),'Partial costume mismatch');counts+=1
 lowhp=0
 for n in range(120,126):
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==stable.composite(n,mask,arm)[0].tobytes(),'Frozen lowHP changed');lowhp+=1
 # UI world-space mapping is independent of its new rectangle bounds.
 uiparts=0
 for n,k in((19,156),(20,157),(21,158)):
  v=a.layer(k)[0];y,x=np.nonzero(v);want=np.zeros_like(v)
  if n in(19,20):want[y+1,319-x]=v[y,x]
  else:want=v.copy()
  need(np.array_equal(world_ui(ui,n),want),'Selection wholebody transform differs')
  for p in aliased_composition(entry(ui,10),2,n)['parts']:
   tile=p['page']*256+p['tile'];pixels=np.frombuffer(tile_pixels(entry(ui,0x10102)[90112:],tile),np.uint8).reshape(16,16)
   need(tile%16!=0 or not pixels[:,0].any(),'Selection GPU horizontal boundary');need(tile%256>=16 or not pixels[0].any(),'Selection GPU top row boundary');uiparts+=1
 rejected=[]
 def reject(name,fn):
  try:fn()
  except(ValueError,AssertionError):rejected.append(name)
  else:raise AssertionError(name+' unexpectedly accepted')
 reject('wrong_original_PL00',lambda:maker.pack(sources['PL00_U.ARC'],desired))
 reject('changed_checkpoint',lambda:maker.pack(bytes([old[0]^1])+old[1:],desired))
 reject('truncated_checkpoint',lambda:maker.pack(old[:-1],desired))
 reject('missing_ref',lambda:maker.pack(old,{n:v for n,v in desired.items()if n!=157}))
 bad={n:{b:v.copy()for b,v in layers.items()}for n,layers in desired.items()};bad[156][0][160,160]=16
 reject('invalid_index',lambda:maker.pack(old,bad))
 badshape={n:{b:v.copy()for b,v in layers.items()}for n,layers in desired.items()};badshape[156][0]=np.zeros((16,16),np.uint8)
 reject('invalid_shape',lambda:maker.pack(old,badshape))
 reject('wrong_selection_source',lambda:patch(old,actual,oldui[:-1],pal))
 reject('wrong_selection_CLUT',lambda:patch(old,actual,oldui,bytes(len(pal))))
 key=next(iter(maker.ART_HASH));saved=maker.ART_HASH[key]
 try:maker.ART_HASH[key]='0'*64;reject('registered_art_hash',lambda:maker.targets(original))
 finally:maker.ART_HASH[key]=saved
 tracepath=H/'fourth_return158/native.json';native=json.loads(tracepath.read_text('utf8'));need(native['executable_sha256']==sha(sources['SLUS_005.61']),'Native trace EXE differs');need(native['source_bin_sha256']==SOURCE_SHA,'Native trace BIN differs')
 case=next(r for r in native['cases']if r['armor']==15 and r['arm_type']==2);trace=case['trace'];refs=[r['ref']for r in trace];calls=[trace[i+1]['tick']-r['tick']if i+1<len(trace)else case['ticks_until_animation4']-r['tick']for i,r in enumerate(trace)]
 def panel(n):
  board=Image.new('RGB',(4*288,384+38),'#1a202b');dr=ImageDraw.Draw(board)
  for col,(label,arc,mask)in enumerate((('base old',original,0),('base new',a,0),('Fourth old',original,15),('Fourth new',a,15))):
   im=arc.composite(n,mask)[0].crop((112,96,208,224)).resize((288,384),Image.Resampling.NEAREST);board.paste(im,(col*288,38),im);dr.text((col*288+6,6),f'{label} {n}',fill='white')
  return board
 frames=[panel(0)]+[panel(n)for n in refs]+[panel(160)]
 for speed,name in((1,'sequence.webp'),(4,'sequence_review_4x.webp')):
  durations=[650]+[round(c*1000/60*speed)for c in calls]+[350];frames[0].save(out/name,save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True)
 write(out/'sequence.json',{'kind':'native_frame_order_simulation_not_gameplay','refs':refs,'actual_native_calls':calls,'native_trace_sha256':sha(tracepath.read_bytes()),'source_executable_sha256':native['executable_sha256'],'fps_assumption':60,'review_slowdown_copy':4,'extra_idle_and_final_hold_for_review':True,'physics_not_simulated':True,'native_trace':tracepath.relative_to(ROOT).as_posix()})
 write(out/'repro_and_rejections.json',{'passed':True,'source_bin_sha256':SOURCE_SHA,'reproduced_PL00':sha(actual),'reproduced_selection':sha(ui),'gpu_boundary_player_parts':parts,'gpu_boundary_selection_parts':uiparts,'native_target_mask_arm_checks':counts,'frozen_lowHP_mask_arm_checks':lowhp,'selection_world_transform_checks':3,'selection_nonselected_frames':22,'rejected_inputs':rejected,'zero_game_or_save_writes':True,'source_bin_unchanged_after':file_hash(SOURCE)==SOURCE_SHA,'runtime_emulator_test':False,'complete_art_unification':False})
 write(out/'FROZEN.json',{'frozen':True,'scope':'새 기본/포스 정면156, 파츠별157/158 귀환, 선택19/20/21 및 이전 저체력120..125 누적','files':{n:sha((out/n).read_bytes())for n in('PL00_U.ARC','ST0E_U1.ARC','proposal.json')},'art_inputs':maker.ART_HASH,'actual_viewed':['base_comparison.png','fourth_comparison.png','partial_156.png','partial_157.png','partial_158.png','selection19_21_comparison.png'],'runtime_verified':False,'not_full_style_completion':True})
 print(json.dumps({'passed':True,'PL00':sha(actual),'selection':sha(ui),'player_parts':parts,'ui_parts':uiparts,'mask_arm':counts,'lowhp_preserved':lowhp,'rejects':len(rejected),'sequence_calls':calls}))

if __name__=='__main__':main()
