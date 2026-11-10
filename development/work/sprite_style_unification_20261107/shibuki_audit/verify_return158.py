"""귀환 준비본 재현/거부/전용 GPU 경계 및 실제 표 순서 시뮬레이션."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import indexed_atlas,decode_stream,composition_frame
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from prepare_return158 import pack,targets
from sync_return158_ui import patch

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');data=read_disc(SOURCE,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0];out=H/'prepared_return158_01'
 rebuilt,proof=pack(data['PL00_U.ARC']);need(rebuilt==(out/'PL00_U.ARC').read_bytes(),'PL00 reproducibility')
 ui,info,_,_=patch(data['PL00_U.ARC'],rebuilt,data['ST0E_U1.ARC'],entry(data['COL0E_U1.ARC'],5));need(ui==(out/'ST0E_U1.ARC').read_bytes(),'Selection reproducibility')
 a=Archive(rebuilt);f=a.banks[0]['frames'][158];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
 parts=0
 for b in(0,5,6,7,8):
  for p in composition_frame(a.c,b,158)['parts']:
   t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t%16!=0 or not tile[:,0].any(),'X GPU edge');need(not p['flip_y']or t//16%16!=0 or not tile[0].any(),'Y GPU edge');parts+=1
 rejected=[]
 tests=[('changed_PL00',lambda:pack(bytes([data['PL00_U.ARC'][0]^1])+data['PL00_U.ARC'][1:])),('truncated_PL00',lambda:pack(data['PL00_U.ARC'][:-1])),('changed_selection',lambda:patch(data['PL00_U.ARC'],rebuilt,bytes([data['ST0E_U1.ARC'][0]^1])+data['ST0E_U1.ARC'][1:],entry(data['COL0E_U1.ARC'],5))),('wrong_selection_palette',lambda:patch(data['PL00_U.ARC'],rebuilt,data['ST0E_U1.ARC'],bytes(len(entry(data['COL0E_U1.ARC'],5)))))]
 for name,fn in tests:
  try:fn()
  except(ValueError,AssertionError):rejected.append(name)
  else:raise AssertionError(name+' was accepted')
 native=json.loads((H/'fourth_return158/native.json').read_text('utf8'));case=next(r for r in native['cases']if r['armor']==15 and r['arm_type']==2);trace=case['trace'];refs=[r['ref']for r in trace];calls=[trace[i+1]['tick']-r['tick']if i+1<len(trace)else case['ticks_until_animation4']-r['tick']for i,r in enumerate(trace)]
 old=Archive(data['PL00_U.ARC']);frames=[];duration=[]
 def pic(n):
  board=Image.new('RGB',(4*288,384+38),'#1a202b');dr=ImageDraw.Draw(board)
  for col,(label,arc,mask)in enumerate((('base before',old,0),('base prepared',a,0),('Fourth before',old,15),('Fourth prepared',a,15))):
   im=arc.composite(n,mask)[0].crop((112,96,208,224)).resize((288,384),Image.Resampling.NEAREST);board.paste(im,(col*288,38),im);dr.text((col*288+6,6),f'{label} ref{n}',fill='white')
  return board
 # Four times slower is intentionally a review aid, not original gameplay timing.
 frames.append(pic(0));duration.append(650)
 for n,c in zip(refs,calls):frames.append(pic(n));duration.append(round(c*1000/60*4))
 frames.append(pic(160));duration.append(350)
 frames[0].save(out/'sequence_review_4x.webp',save_all=True,append_images=frames[1:],duration=duration,loop=0,lossless=True)
 write(out/'sequence.json',{'kind':'native_frame_order_simulation_not_gameplay','refs':refs,'actual_native_calls':calls,'fps_assumption':60,'review_slowdown':4,'extra_idle_and_final_hold_for_review':True,'physics_not_simulated':True,'native_trace':'../fourth_return158/native.json'})
 write(out/'repro_and_rejections.json',{'passed':True,'source_bin_sha256':SOURCE_SHA,'reproduced_PL00':sha(rebuilt),'reproduced_selection':sha(ui),'gpu_boundary_parts':parts,'rejected_inputs':rejected,'runtime_emulator_test':False,'complete_art_unification':False,'partial_mask_checks':32,'zero_game_or_save_writes':True})
 print(json.dumps({'passed':True,'sha':sha(rebuilt),'ui':sha(ui),'gpu_parts':parts,'rejected':len(rejected),'native_refs':refs,'calls':calls}))
if __name__=='__main__':main()
