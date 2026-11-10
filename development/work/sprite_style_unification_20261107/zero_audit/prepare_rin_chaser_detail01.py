"""체이서4각도/4리본파형/원래진동 관계를 현재 자원에서 확인해 원화 입력을 준비한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
D=Path(__file__).parent/'rin_extension';O=D/'chaser_detail01';O.mkdir(exist_ok=False);P=D/'prepared_bank1_recovery128/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89'
g=entry(arc,2);ps=entry(arc,3);pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32);families={14:list(range(14,22)),22:list(range(22,30)),30:list(range(30,38)),38:list(range(38,42))};frames={};masters=[]
def layer(raw,count,c):
 if not c['parts']:return np.zeros((384,384),np.uint8)
 p,size,bb,_=compose_indices(raw,count,c,allowed_cluts={0});a=np.frombuffer(p,np.uint8).reshape(size[1],size[0]);w=np.zeros((384,384),np.uint8);w[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=a;return w
sheet=Image.new('RGBA',(192,128));crop=(112,120,208,184);parts_proofs=[]
for i,(base,ids)in enumerate(families.items()):
 fs=graphics_bank(g,1)['frames'];off=fs[base]['offset'];assert [f['index']for f in fs if f['offset']==off]==ids;count=fs[base]['tile_count'];raw=decode_stream(g,off,fs[base]['limit'],count*128).data;cs={n:composition_frame(ps,5,n)for n in ids};owned=set.intersection(*[{p['tile']for p in c['parts']}for c in cs.values()]);bodies={};tails={};refbody=None
 for k,n in enumerate(ids):
  phase=[0,1,2,3,1,2,3,1][k];dy=[0,0,0,0,1,2,1,-1][k];c=cs[n];body=layer(raw,count,{**c,'parts':[p for p in c['parts']if p['tile']in owned]});tail=layer(raw,count,{**c,'parts':[p for p in c['parts']if p['tile']not in owned]});z=np.where(body,body,tail).astype(np.uint8);actual=render(arc,1,5,n)[0];assert np.array_equal(z,actual)
  fixed=np.roll(body,-dy,axis=0)
  if refbody is None:refbody=fixed
  assert np.array_equal(refbody,fixed),'Body differs beyond known native bob'
  bodies[n]=body;tails[n]=tail;Image.fromarray(body).save(O/f'b1_{n:03}_body_indices.png');Image.fromarray(tail).save(O/f'b1_{n:03}_ribbon_indices.png');Image.fromarray(actual).save(O/f'b1_{n:03}_full_indices.png')
  frames[f'b1_{n:03}']={'body_master':base,'ribbon_phase':phase,'original_bob_y':dy,'tile_count':count,'part_count':len(c['parts']),'world_bbox':list(rgba(actual,pal).getbbox()),'body_tiles':sorted(owned),'ribbon_tiles':sorted({p['tile']for p in c['parts']}-owned),'raw_sha256':sha(raw),'body_sha256':sha(body.tobytes()),'ribbon_sha256':sha(tail.tobytes()),'body_equal_after_bob_removed':True}
 rgba(refbody,pal).crop(crop).save(O/f'body_{base}_native.png');rgba(render(arc,1,5,base)[0],pal).crop(crop).save(O/f'full_{base}_native.png');sheet.paste(rgba(refbody,pal).crop(crop),(i%2*96,i//2*64));masters.append({'ref':base,'cell':[i%2,i//2],'body_aliases':ids,'body_tiles':sorted(owned),'body_origin':[160,160],'world_crop':list(crop),'native_canvas':[96,64]})
 parts_proofs.append({'master':base,'shared_refs':ids,'body_common_tiles':sorted(owned),'original_tile_count':count,'source_stream_offset':off})
sheet.save(O/'input_native.png');sheet.resize((1536,1024),Image.Resampling.NEAREST).save(O/'input.png')
# Full accepted idle remains visible; no partial head crop is used as style reference.
rgba(render(arc,0,0,147)[0],pal).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST).save(O/'idle_full_reference.png')
rgba(render(arc,0,0,8)[0],pal).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST).save(O/'new_run8_detail_reference.png')
pages=[]
for form,words in [('normal',pal),('black',black)]:
 board=Image.new('RGB',(1536,1024),(28,34,45));dr=ImageDraw.Draw(board)
 for i,base in enumerate(families):
  for col,layername in enumerate(('full','body','ribbon')):
   z=np.array(Image.open(O/f'b1_{base:03}_{layername}_indices.png'));p=rgba(z,words).crop(crop).resize((480,320),Image.Resampling.NEAREST);x=col*512;y=i*256;view=p.crop((0,0,480,256))
   # The full64px crop is shown at4x, never clipped to the board row.
   p=rgba(z,words).crop(crop).resize((384,256),Image.Resampling.NEAREST);board.paste(p,(x,y),p);dr.text((x+4,y+4),f'{base} {layername}',fill='white')
 board.save(O/f'{form}_source_layers.png');pages.append(str((O/f'{form}_source_layers.png').relative_to(ROOT)))
r={'source':str(P.relative_to(ROOT)),'source_sha256':sha(arc),'master_count':4,'target_ref_count':28,'native_sheet_size':[192,128],'scale':8,'masters':masters,'frames':frames,'shared_streams':parts_proofs,'original_ribbon_phase_order':[0,1,2,3,1,2,3,1],'original_bob_y':[0,0,0,0,1,2,1,-1],'last_family_uses_first4_only':True,'source_layer_sheets':pages,'scope':'현체이서28참조는4몸체각도와4리본파형/원래진동으로 구성됩니다. 이번입력은 몸체만이며 리본은별도보존해 새몸체의등접점과 검증한뒤 연결합니다.아직새원화/패킹/실기없음.'}
(O/'inputs.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'families':parts_proofs,'refs':len(frames)}))
