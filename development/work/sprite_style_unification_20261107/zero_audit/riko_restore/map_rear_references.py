"""Find exact existing rear-head master usage across every displayable Zero ref."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,composition_frame
arc=(D/'prepared_v1/PL01_U.ARC').read_bytes();assert hashlib.sha256(arc).hexdigest()=='118f04c93c716a36138f903c32d260be2ffa3c6c951cf4993ea93b1f48d249da'
template=np.array(Image.open(ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png'));mask=np.isin(template,[4,8,14]);g,c=entry(arc,2),entry(arc,3);rows=[];checked=0;partial=[]
for b in (0,1):
 bank=graphics_bank(g,b);sharing=defaultdict(list)
 for f in bank['frames']:sharing[f['offset']].append(f['index'])
 for f in bank['frames']:
  n=f['index'];pb=0 if b==0 else 5
  if b==1 and 42<=n<=49:partial.append(f'b{b}_{n:03d}');continue
  a=render(arc,b,pb,n)[0];checked+=1
  for variant,head,hm in [('rear',template,mask),('rear_mirrored',np.fliplr(template),np.fliplr(mask))]:
   values,counts=np.unique(head[hm],return_counts=True);color=int(values[np.argmin(counts)]);sy,sx=np.argwhere(hm&(head==color))[0]
   for py,px in np.argwhere(a==color):
    x,y=int(px-sx),int(py-sy)
    if x<0 or y<0 or x+23>384 or y+19>384:continue
    window=a[y:y+19,x:x+23]
    if not np.array_equal(window[hm],head[hm]):continue
    cp=composition_frame(c,pb,n);rows.append({'id':f'b{b}_{n:03d}','bank':b,'parts_bank':pb,'ref':n,'view':variant,'old_template_origin_world':[x-160,y-160],'old_template_size':[23,19],'green_pixels_exact':int(hm.sum()),'template_opaque_pixels':int((head>0).sum()),'all_template_opaque_exact':bool(np.array_equal(window[head>0],head[head>0])),'shared_raw_refs':sharing[f['offset']],'stream_offset':f['offset'],'tile_count':f['tile_count'],'part_count':len(cp['parts'])})
groups={}
for r in rows:groups.setdefault(f"bank{r['bank']}_{r['view']}",[]).append(r['ref'])
report={'source_arc_sha256':hashlib.sha256(arc).hexdigest(),'template':'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png','template_sha256':hashlib.sha256((ROOT/'work/ver_buki_riko/art_pilot/ladder_v1/rear_head_indexed.png').read_bytes()).hexdigest(),'checked_display_refs':checked,'partial_vram_excluded':partial,'matching_rule':'마스터의 녹색141px 전체가 정확 일치. 머리 밖의 손·어깨 사각형은 검색 조건에서 제외. 원본/좌우반전 모두 검사.','matched_references':len(rows),'groups':groups,'frames':rows,'new_head_registration_not_performed':True}
(D/'rear_master_references.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'checked':checked,'matched':len(rows),'groups':groups}))
