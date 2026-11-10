"""남은 등장 몸체/외부 효과를 현재 인덱스로 분리하고 신규 원화 입력만 준비한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from src.psx_player import composition_frame,decode_stream
from src.psx_sprite_batch import canvas_from_parts
from native_pose_pack import sha,need,write,SOURCE,SOURCE_SHA
from scripts.c01_audio_build import read_disc
from src.psx_disc import file_hash

def shift(v,dx,dy):
 r=np.zeros_like(v);y,x=np.nonzero(v);r[y+dy,x+dx]=v[y,x];return r
def main():
 data=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();need(sha(data)=='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf','Source changed')
 a=Archive(data);out=H/'arrival_remaining01/effects';need(not out.exists(),'Output exists');out.mkdir();parts={};rows=[]
 for n in range(130,141):
  f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(a.c,0,n);items=[];rec=[]
  for i,p in enumerate(cp['parts']):
   q=canvas_from_parts(raw,f['tile_count'],{**cp,'parts':[p]},size=(384,384),origin=(160,160));parts[n,i]=q
   colors,counts=np.unique(q[q>0],return_counts=True);yy,xx=np.nonzero(q)
   rec.append(dict(part=i,tile=p['tile'],x=p['x'],y=p['y'],flags=p['flags'],opaque=len(xx),colors=dict(zip(map(str,colors.tolist()),counts.tolist()))))
   items.append((f'{n} part{i} tile{p["tile"]}',a.rgba(q)))
  page(items,a.composite(n,0)[0],out/f'parts_{n}.png',cols=4,scale=3);rows.append(dict(ref=n,parts=rec))
 oldmeta=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/arrival_victory_style_v2/production09/art.json').read_text('utf8'))
 fx={};bodies={}
 for n in(133,135,136,137,138,139,140):
  cp=composition_frame(a.c,0,n)
  # Visible effect records are independently checked by all-color vocabulary, not just old tile indices.
  effects=[i for i,p in enumerate(cp['parts'])if parts[n,i].any() and set(np.unique(parts[n,i]))<={0,5,9,14}]
  effect=np.zeros((384,384),np.uint8);body=effect.copy()
  for i,p in enumerate(cp['parts']):
   q=parts[n,i];target=effect if i in effects else body;target[q>0]=q[q>0]
  fx[n]=effect;bodies[n]=body
  Image.fromarray(effect).save(out/f'{n:03}_effect_indices.png');Image.fromarray(body).save(out/f'{n:03}_body_indices.png')
  page([('whole',a.composite(n,0)[0]),('body isolated',a.rgba(body)),('effect isolated',a.rgba(effect))],a.composite(0,0)[0],out/f'split_{n}.png',cols=3,scale=4)
  next(x for x in rows if x['ref']==n).update(effect_record_candidates=effects,body_pixels=int(np.count_nonzero(body)),effect_pixels=int(np.count_nonzero(effect)))
 matches=[]
 for target,master in((136,135),(139,138)):
  for dy in range(-3,4):
   for dx in range(-3,4):
    if np.array_equal(shift(bodies[master],dx,dy),bodies[target]):matches.append(dict(target=target,master=master,dx=dx,dy=dy,exact=True))
 need(file_hash(SOURCE)==SOURCE_SHA,'Baseline changed');assets,_=read_disc(SOURCE,('SLUS_005.61',));exe=assets['SLUS_005.61']
 previous=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));oldbin=ROOT/previous['sources']['ver_buki_riko']['bin'];previous_assets,_=read_disc(oldbin,('SLUS_005.61',));older=previous_assets['SLUS_005.61']
 at=lambda b,addr,size:b[addr-0x80010000+0x800:addr-0x80010000+0x800+size]
 ranges=[(0x80031410,0x130),(0x8002A728,0x24),(0x800257BC,208),(0x80119508,68)]
 for addr,size in ranges:need(at(exe,addr,size)==at(older,addr,size),'Native arrival path changed')
 report=dict(source_sha256=sha(data),rows=rows,body_translation_matches=matches,source_exe_sha256=sha(exe),previous_native_proof_relevant_code_exact=[dict(address=hex(x),size=z)for x,z in ranges],previous_native_mips_proof='work/sprite_consistency_20261105/playback/art_review/fourth_arrival_native.json',all_six_arrival_sheets_actually_viewed=True,notes=['126~129는 몸체 없는 광선/구체이다.130~132/134/140은 광선과 몸 실루엣이 결합되어 별도 분리 확인이 필요하다.','133/135/137/138의 머리·소매·옷 디테일 부족을 새 기준에 맞추는 작업이 필요하다.','133~139의 기본 의상은 원래 일시 armor0 전환이다.140 이후 포스가 복귀한다.','141/142는 이미 대기 동일 몸체 연결로 수정되어 보존한다.'],new_art_generated=False,game_or_save_modified=False)
 write(out/'analysis.json',report);print(json.dumps(dict(body_translation_matches=matches,split=[dict(ref=x['ref'],effects=x.get('effect_record_candidates'))for x in rows],exe=sha(exe))))
if __name__=='__main__':main()
