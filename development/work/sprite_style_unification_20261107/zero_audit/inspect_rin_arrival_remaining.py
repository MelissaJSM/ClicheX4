"""잔여 등장5몸체·흰 섬광2의 실제 색인/공유를 읽기 조사한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame
R=Path(__file__).parent/'rin_extension';P=R/'prepared_chaser01/PL01_U.ARC';O=R/'arrival_remaining_probe01';O.mkdir(exist_ok=False);a=P.read_bytes();pal=struct.unpack_from('<16H',entry(a,9));g=entry(a,2);ps=entry(a,3);rows=[];arrays={}
for n in range(247,254):
 v=render(a,0,0,n)[0];arrays[n]=v;f=graphics_bank(g,0)['frames'][n];c=composition_frame(ps,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;Image.fromarray(v).save(O/f'b0_{n:03}_indices.png');rows.append({'ref':n,'bbox':rgba(v,pal).getbbox(),'pixels':int(np.count_nonzero(v)),'colors':np.unique(v).tolist(),'tile_count':f['tile_count'],'part_count':len(c['parts']),'raw_sha256':hashlib.sha256(raw).hexdigest(),'stream_offset':f['offset'],'parts':[{k:p[k]for k in('tile','x','y','flags')}for p in c['parts']]})
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(a,9),row*32);sh=Image.new('RGB',(1536,720),(28,34,45));dr=ImageDraw.Draw(sh)
 for i,n in enumerate([147,*range(247,254)]):
  v=render(a,0,0,n)[0];p=rgba(v,words).crop((112,104,208,192)).resize((384,352),Image.Resampling.NEAREST);x=i%4*384;y=i//4*360;sh.paste(p,(x,y+8),p);dr.text((x+4,y+4),str(n),fill='white')
 sh.save(O/f'{form}_sources.png')
diffs=[]
for n in range(249,254):
 for m in range(n+1,254):diffs.append({'refs':[n,m],'exact':bool(np.array_equal(arrays[n],arrays[m])),'changed_pixels':int(np.count_nonzero(arrays[n]!=arrays[m])),'alpha_difference':int(np.count_nonzero((arrays[n]>0)!=(arrays[m]>0)))})
j={'source':str(P.relative_to(ROOT)),'source_sha256':hashlib.sha256(a).hexdigest(),'refs':rows,'pair_comparisons':diffs,'scope':'미술 원화 제작 전 읽기 비교. 원섬광247/248을 인물로 재작화하지 않는다.'};(O/'inventory.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'refs':[{k:r[k]for k in('ref','bbox','tile_count','part_count','pixels','colors')}for r in rows],'pairs':diffs}))
