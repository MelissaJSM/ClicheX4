"""새 몸의 인덱스 마스크로 피격 섬광을 변환하고 원래 외부 불꽃을 유지한다."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent;a=d/'production02';art=json.loads((a/'art.json').read_text());plan=json.loads((d/'plan.json').read_text());source=ROOT/Path(art['source_inventory']).parent;inv=json.loads((source/'inventory.json').read_text())
parent=ROOT/'out/ver_buki_riko/shibuki_wall_20261026T135224131979Z';arc=(parent/'modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==9)
import struct
pal2=list(struct.unpack('<16H',arc[e['offset']+64:e['offset']+96]));art['effect_palette_words']=pal2
def original(n):
 im=Image.open(source/f'base_{n:03d}.png');v=np.array(im);bb=inv['base_frames'][n]['bounds'];canvas=np.zeros((80,96),np.uint8);yy,xx=np.nonzero(v);canvas[yy+bb[1]+40,xx+bb[0]+48]=v[yy,xx]%16;return canvas
def dilate(mask):
 padded=np.pad(mask,1);return np.logical_or.reduce([padded[dy:dy+80,dx:dx+96] for dy,dx in ((1,1),(0,1),(2,1),(1,0),(1,2))])
normal=np.array(Image.open(a/'frame_106.png'));launch=np.array(Image.open(a/'frame_110.png'));old=original(110)!=0;new=launch!=0
flash=np.zeros_like(normal);flash[dilate(normal!=0)]=9;flash[normal!=0]=14
targets={109:flash}
for n in (112,113,114):
 orig=original(n);out=orig.copy();out[dilate(dilate(old))]=0
 if n==114:out[np.isin(out,[3,5])]=0
 if n==112:
  out[dilate(new)]=6;out[new]=14
 elif n==113:out[dilate(new)]=1
 else:
  out[dilate(new)]=1;out[new]=3;out[np.isin(launch,[1,2,4,8,15])]=5;out[np.isin(launch,[6,9])]=1
 targets[n]=out
for n,im in targets.items():
 save_image(im.tobytes(),(96,80),art['palette_words'] if n==109 else pal2,a/f'frame_{n:03d}.png')
 art['frames'].append({'frame':n,'image':f'frame_{n:03d}.png','derived_from':106 if n==109 else 110,'effect_conversion':'normal flash uses new alpha; flame variants retain original rays outside old-body dilation and use new body silhouette'})
art['frames'].sort(key=lambda r:r['frame']);(a/'art.json').write_text(json.dumps(art,indent=2),encoding='utf-8')
layouts=[]
for r in plan['groups']:
 n=r['frame'];mask=np.array(Image.open(a/f'frame_{n:03d}.png'))!=0;layout=cover(mask,len(r['writable']),15);layout.update(frame=n);layouts.append(layout);print({'frame':n,'fits':layout['fits'],'rects':len(layout['rects'])},flush=True)
(a/'layout.json').write_text(json.dumps(layouts,indent=2),encoding='utf-8')
sheet=Image.new('RGB',(3*288,2*264),'#28394b');draw=ImageDraw.Draw(sheet)
for i,n in enumerate((106,109,110,112,113,114)):
 im=Image.open(a/f'frame_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=i%3*288;y=i//3*264;sheet.paste(im,(x,y+24),im);draw.text((x+8,y+5),str(n),fill='white')
sheet.save(a/'effects_review.png')
