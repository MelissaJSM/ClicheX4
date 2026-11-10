"""Read-only pose-sharing analysis for Rin's third ground strike."""
from pathlib import Path
import sys,json,hashlib,struct,itertools
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,composition_frame
D=Path(__file__).parent;O=D/'rin_extension/third_saber_analysis';O.mkdir(exist_ok=True)
P=D/'rin_extension/prepared_burst_pair_final_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
pal=struct.unpack_from('<16H',entry(arc,9));bank=graphics_bank(entry(arc,2),0)
refs=list(range(109,128,2));arrays={n:render(arc,0,0,n)[0] for n in refs};groups=[]
for n,a in arrays.items():
 for group in groups:
  if np.array_equal(a,arrays[group[0]]):group.append(n);break
 else:groups.append([n])
def bbox(mask):
 y,x=np.nonzero(mask)
 return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)] if len(x) else None
rows={}
for n,a in arrays.items():
 Image.fromarray(a).save(O/f'b0_{n:03}_indices.png')
 f=bank['frames'][n];c=composition_frame(entry(arc,3),0,n)
 rows[str(n)]={'world_bbox':bbox(a!=0),'pixels':int(np.count_nonzero(a)),
              'canvas_sha256':sha(a.tobytes()),'graphics':f,'composition':c}
pairs=[]
for a,b in itertools.combinations([g[0] for g in groups],2):
 diff=arrays[a]!=arrays[b]
 pairs.append({'a':a,'b':b,'different_pixels':int(diff.sum()),'difference_bbox':bbox(diff),
               'by_y_band':{f'{lo}:{hi}':int(diff[lo:hi].sum()) for lo,hi in [(110,140),(140,152),(152,166),(166,184),(184,200)]}})
crop=(120,112,208,200);scale=6;cw=88*scale;ch=cw+30
for variant in('normal','black'):
 words=pal if variant=='normal' else struct.unpack_from('<16H',entry(arc,9),13*32)
 sheet=Image.new('RGB',(cw*3,ch*2),'#3e4956');draw=ImageDraw.Draw(sheet)
 for i,n in enumerate([147]+[g[0] for g in groups]):
  a=render(arc,0,0,n)[0];pic=rgba(a,words).crop(crop).resize((cw,cw),Image.Resampling.NEAREST)
  x=i%3*cw;y=i//3*ch;sheet.paste(pic,(x,y+30),pic);draw.text((x+8,y+8),f'IDLE {n}' if n==147 else f'b0_{n:03}',fill='white')
 sheet.save(O/f'{variant}_unique.png')
report={'source':str(P.relative_to(ROOT)),'source_sha256':sha(arc),'refs':refs,
        'same_canvas_groups':groups,'same_canvas_group_count':len(groups),'rows':rows,'pair_differences':pairs,
        'independent_of_riko_group_assumptions':True,'original_game_or_frozen_candidate_changed':False,
        'regional_semantic_claim':'y帯の差分数は手/衣装の意味を自動確定しない。実画像で別途判断。'}
(O/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'groups':groups,'pairs':pairs},ensure_ascii=False))
