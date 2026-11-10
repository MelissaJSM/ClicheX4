"""등장 후보 재현/입력거부/광선/시간표/이전 수정 전수 보존을 검사한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from src.psx_player import indexed_atlas,decode_stream,composition_frame
from src.psx_disc import file_hash
from register_ladder_parts import compose
from probe_arrival_silhouettes import parts
import prepare_arrival_complete as maker

def main():
 out=H/'prepared_arrival_victory01';parent=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();data=(out/'PL00_U.ARC').read_bytes();ui=(out/'ST0E_U1.ARC').read_bytes()
 need(sha(data)=='78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e','Candidate changed');need(ui==(H/'prepared_victory_ladder01/ST0E_U1.ARC').read_bytes(),'Selection changed')
 need(file_hash(SOURCE)==SOURCE_SHA,'Baseline changed');source=read_disc(SOURCE,('PL00_U.ARC','SLUS_005.61'))[0]
 desired,provenance=maker.targets(parent);again,repro=maker.pack(parent,desired);need(again==data,'Reproduction mismatch')
 a=Archive(data);old=Archive(parent);layers=gpu=masks=stable=0
 for n in sorted(maker.REFS|{132}):
  f=a.banks[0]['frames'][n];need(f['tile_count']==32,'Tile count');raw=decode_stream(a.g,f['offset'],f['limit'],4096).data;atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
  for b in(0,5,6,7,8):
   want=desired[n][b]if n in desired else old.layer(n,b)[0];need(np.array_equal(a.layer(n,b)[0],want),'Indexed target mismatch');layers+=1
   for p in composition_frame(a.c,b,n)['parts']:
    t=p['tile'];need(t<32,'Tile overflow');tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    need(t%16!=0 or not tile[:,0].any(),'U boundary');need(not p['flip_y']or t//16%16!=0 or not tile[0].any(),'V boundary');gpu+=1
  for mask in range(16):
   for arm in(1,2):
    target=compose(a,desired[n],mask)if n in desired else old.composite(n,mask,arm)[0]
    need(a.composite(n,mask,arm)[0].tobytes()==target.tobytes(),'Mask/arm readback');masks+=1
 for n in(*range(55,67),*range(120,126),*range(143,159),183,*range(204,208),0,*range(115,120),140,141,142):
  for mask in range(16):
   for arm in(1,2):need(a.composite(n,mask,arm)[0].tobytes()==old.composite(n,mask,arm)[0].tobytes(),'Frozen earlier group changed');stable+=1
 for n,ids in((136,[7,8]),(137,[6,8])):
  effect=parts(old,n,ids);need(np.array_equal(a.layer(n)[0][effect>0],effect[effect>0]),'Native external sparks changed')
 oldbody=parts(old,131,range(16,24));newbody=desired[133][0]>0;region=(oldbody>0)|newbody
 for n in(130,131):need(np.array_equal(a.layer(n)[0][~region],old.layer(n)[0][~region]),'Outer energy changed')
 for n in(126,127,128,129,132,140,141,142):need(np.array_equal(a.layer(n)[0],old.layer(n)[0]),'Unchanged arrival image differs')
 rejected=[]
 def reject(name,fn):
  try:fn()
  except(ValueError,AssertionError,KeyError):rejected.append(name)
  else:raise AssertionError('Invalid input accepted: '+name)
 reject('wrong_parent',lambda:maker.pack(source['PL00_U.ARC'],desired));reject('truncated_parent',lambda:maker.pack(parent[:-1],desired));reject('modified_parent',lambda:maker.pack(bytes([parent[0]^1])+parent[1:],desired))
 reject('missing_ref',lambda:maker.pack(parent,{n:v for n,v in desired.items()if n!=133}));reject('extra_ref',lambda:maker.pack(parent,{**desired,142:desired[133]}))
 for name,v in(('index16',16),('wrong_pixel',1)):
  bad={n:{b:q.copy()for b,q in row.items()}for n,row in desired.items()};bad[138][0][0,0]=v;reject(name,lambda:maker.pack(parent,bad))
 for name,v in(('shape',np.zeros((16,16),np.uint8)),('dtype',np.zeros((384,384),np.int16))):
  bad={n:{b:q.copy()for b,q in row.items()}for n,row in desired.items()};bad[138][0]=v;reject(name,lambda:maker.pack(parent,bad))
 exe=source['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0];inventory=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'))
 sequences=[q for q in inventory['animations']if q['id']in(2,95,96)];steps=0
 for seq in sequences:
  frames=[];dur=[]
  for s in seq['steps']:
   off=0x800+int(s['address'],16)-load;need(exe[off:off+4].hex()==s['bytes'],'Native step changed');steps+=1;n=s['frame']
   im=Image.new('RGB',(1024,340),'#1a202b');draw=ImageDraw.Draw(im)
   for col,(label,arc,owned)in enumerate((('base before',old,0),('base new',a,0),('fourth before',old,15),('fourth new',a,15))):
    mask=0 if seq['id']==2 and s['position']<14 else owned
    pic=arc.composite(n,mask)[0].crop((128,120,192,200)).resize((256,320),Image.Resampling.NEAREST);im.paste(pic,(col*256,20),pic);draw.text((col*256+3,4),f'{label} ref{n} mask{mask:X}',fill='white')
   frames.append(im);dur.append(round(s['duration_calls_uninterrupted']*1000/60))
  for slow in(1,4):frames[0].save(out/f'animation{seq["id"]:03}_{slow}x.webp',save_all=True,append_images=frames[1:],duration=[t*slow for t in dur],loop=0,lossless=True)
 write(out/'sequences.json',dict(source_exe_sha256=sha(exe),animations=sequences,actual_step_bytes_checked=steps,calls_per_second_assumption=60,arrival_armor_policy='ID2 위치0~13은 일시적 아머0, 위치14부터 소유 아머를 표시한다. 기존87call MIPS 근거와 동일 코드다.',events_executed=False,physics_executed=False,actual_gameplay=False,terminal_policy='검토 영상은 표시 스텝을 한 번 재생한 뒤 반복한다. 실제 event·idle 전환·특수무기 오브젝트는 실행하지 않음.'))
 report=dict(passed=True,source_bin_sha256=SOURCE_SHA,parent_sha256=sha(parent),candidate_sha256=sha(data),selection_sha256=sha(ui),reproduction_exact=True,indexed_layers=layers,gpu_parts=gpu,mask_arm_checks=masks,prior_frozen_mask_arm_checks=stable,raw_checks=repro['decoded_references'],nonselected_composites=repro['nonselected_composites'],nonselected_part_records=repro['preserved_part_records'],external_sparks_exact=True,outer_energy_exact_outside_body_union=True,shared132_same_display=True,selection_unchanged=True,native_animation_steps=steps,rejected_inputs=rejected,readback_visually_reviewed=['base_comparison.png','fourth_comparison.png','effects_comparison.png','partial_138.png','partial_139.png'],source_unchanged=file_hash(SOURCE)==SOURCE_SHA,actual_emulator_or_mips_test=False,full_art_unification_complete=False)
 write(out/'repro_and_rejections.json',report);print(json.dumps(report))
if __name__=='__main__':main()
