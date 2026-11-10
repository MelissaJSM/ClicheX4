"""승리 누적 자원 무손실 재현·원표·이전수정 보존·입력거부 검사."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import indexed_atlas,decode_stream,composition_frame
from src.psx_disc import file_hash
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from register_ladder_parts import compose
import prepare_victory_complete as maker
from sync_victory_selection import patch as patch_ui

def main():
 out=H/'prepared_victory_ladder01';parent=(H/'prepared_ladder_wall_front02/PL00_U.ARC').read_bytes();data=(out/'PL00_U.ARC').read_bytes();old_ui=(H/'prepared_ladder_wall_front02/ST0E_U1.ARC').read_bytes();ui=(out/'ST0E_U1.ARC').read_bytes()
 need(sha(data)=='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf','Output changed');need(sha(ui)=='5afaa5877976c2d6c7ae38a3061c8b74401a04edaa6e8d639399c53028873695','UI changed')
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed');sources=read_disc(SOURCE,('PL00_U.ARC','COL0E_U1.ARC','SLUS_005.61'))[0];pal=entry(sources['COL0E_U1.ARC'],5)
 desired=maker.targets();rebuilt,repro=maker.pack(parent,desired);need(rebuilt==data,'Game reproduction differs');new_ui,uiproof,_,_=patch_ui(parent,data,old_ui,pal);need(new_ui==ui,'UI reproduction differs')
 a=Archive(data);before=Archive(parent);layers=parts=masks=stable=0
 for n in sorted(maker.REFS):
  f=a.banks[0]['frames'][n];need(f['tile_count']==32,'Native allocation mismatch');raw=decode_stream(a.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
  for b in(0,5,6,7,8):
   need(np.array_equal(a.layer(n,b)[0],desired[n][b]),'Exact indexed art differs');layers+=1
   for q in composition_frame(a.c,b,n)['parts']:
    t=q['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t<32,'Tile overflow')
    need(t%16!=0 or not tile[:,0].any(),'GPU U edge');need(not q['flip_y']or t//16%16!=0 or not tile[0].any(),'GPU V edge');parts+=1
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==compose(a,desired[n],mask).tobytes(),'Partial costume differs');masks+=1
 for n in(*range(55,67),*range(120,126),*range(143,159),183):
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==before.composite(n,mask,arm)[0].tobytes(),'Earlier frozen group differs');stable+=1
 rejected=[]
 def reject(name,fn):
  try:fn()
  except(ValueError,AssertionError,KeyError):rejected.append(name)
  else:raise AssertionError('Invalid input accepted: '+name)
 reject('wrong_parent',lambda:maker.pack(sources['PL00_U.ARC'],desired));reject('truncated_parent',lambda:maker.pack(parent[:-1],desired));reject('changed_parent',lambda:maker.pack(bytes([parent[0]^1])+parent[1:],desired))
 reject('missing_ref',lambda:maker.pack(parent,{n:v for n,v in desired.items()if n!=204}));reject('extra_ref',lambda:maker.pack(parent,{**desired,203:desired[204]}))
 for name,value in [('wrong_index',16),('changed_pixel',1)]:
  bad={n:{b:v.copy()for b,v in z.items()}for n,z in desired.items()};bad[204][0][0,0]=value;reject(name,lambda:maker.pack(parent,bad))
 for name,value in [('wrong_shape',np.zeros((16,16),np.uint8)),('wrong_dtype',np.zeros((384,384),np.int16))]:
  bad={n:{b:v.copy()for b,v in z.items()}for n,z in desired.items()};bad[204][0]=value;reject(name,lambda:maker.pack(parent,bad))
 reject('wrong_ui_parent',lambda:patch_ui(parent,data,bytes([old_ui[0]^1])+old_ui[1:],pal));badpal=bytearray(pal);badpal[512]^=1;reject('wrong_ui_clut',lambda:patch_ui(parent,data,old_ui,bytes(badpal)))
 animation=json.loads((H/'victory_inputs01/manifest.json').read_text('utf8'))['animation'];exe=sources['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0]
 for s in animation['steps']:
  off=0x800+int(s['address'],16)-load;need(exe[off:off+4].hex()==s['bytes'],'Native animation bytes differ')
 def panel(n):
  im=Image.new('RGB',(1024,340),'#1a202b');d=ImageDraw.Draw(im)
  for col,(text,arc,mask)in enumerate((('base before',before,0),('base new',a,0),('fourth before',before,15),('fourth new',a,15))):
   v=arc.composite(n,mask)[0].crop((128,120,192,200)).resize((256,320),Image.Resampling.NEAREST);im.paste(v,(256*col,20),v);d.text((256*col+4,4),f'{text} ref{n}',fill='white')
  return im
 frames=[panel(s['frame'])for s in animation['steps']];dur=[round(s['duration_calls_uninterrupted']*1000/60)for s in animation['steps']]
 for slow in(1,4):frames[0].save(out/f'animation039_{slow}x.webp',save_all=True,append_images=frames[1:],duration=[x*slow for x in dur],loop=0,lossless=True)
 write(out/'sequences.json',dict(actual_executable_sha256=sha(exe),animation=animation,calls_per_second_assumption=60,actual_step_records_checked=6,events_executed=False,gameplay=False,terminal_policy='검토 영상은6스텝을한번표시뒤반복. 실제 event128·말단지속·귀환전환은 실행하지 않음.'))
 report=dict(passed=True,source_bin_sha256=SOURCE_SHA,parent_sha256=sha(parent),reproduced_arc_sha256=sha(data),reproduced_ui_sha256=sha(ui),indexed_layers=layers,partial_mask_arm_checks=masks,gpu_parts=parts,frozen_previous_group_mask_arm_checks=stable,decoded_references=repro['decoded_references'],nonselected_composites=repro['nonselected_composites'],preserved_part_records=repro['preserved_part_records'],selection18_game207_transform_exact=True,other_selection_frames=uiproof['unchanged_frame_count'],native_animation_steps=6,rejected_inputs=rejected,source_unchanged_after=file_hash(SOURCE)==SOURCE_SHA,emulator_test=False,not_full_style_completion=True)
 write(out/'repro_and_rejections.json',report);print(json.dumps(report))
if __name__=='__main__':main()
