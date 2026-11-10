"""생성 그림의 몸통과 승인된 버스터 레이어를 같은 좌표계에 등록한다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent;src=d/'normalized02';out=d/'production05';out.mkdir(exist_ok=True)
art=json.loads((src/'art.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text());original=ROOT/Path(art['source_inventory']).parent
arm=np.array(Image.open(d.parent/'standing_buster_v1/production03/registered_arm_085.png'));arm[40:]=0
yy,xx=np.nonzero(arm==4);edge=xx==xx.min();anchor=np.array([int(xx.min()),float(np.median(yy[edge]))])
# 앞팔 분리 마스크. 손/소매만 제거하며 생성된 얼굴, 귀와 뒷팔은 보존한다.
polys={33:[(0,34),(43,34),(43,44),(0,44)],35:[(0,31),(43,31),(43,43),(0,43)],
37:[(0,22),(42,22),(44,29),(44,37),(0,37)],
39:[(0,12),(48,12),(48,21),(44,26),(0,26)],
41:[(0,9),(49,9),(49,18),(46,18),(45,27),(0,27)],
43:[(0,9),(47,9),(47,22),(44,26),(0,26)],
45:[(0,29),(45,29),(45,40),(0,40)],47:[(0,33),(46,33),(46,43),(0,43)],
49:[(0,32),(45,32),(45,43),(0,43)],51:[(0,34),(46,34),(46,46),(0,46)],53:[(0,38),(45,38),(45,51),(0,51)]}
sheet=Image.new('RGB',(6*288,4*264),'#28394b');draw=ImageDraw.Draw(sheet);records=[];arts=[]
for i,n in enumerate(range(33,55,2)):
 a=np.array(Image.open(src/f'air_{n:03d}.png'));dy=0
 if n>=49:
  dy=62-int(np.nonzero(a)[0].max());a=np.roll(a,dy,axis=0)
  polys[n]={49:[(0,34),(43,34),(43,39),(42,42),(43,44),(42,46),(40,49),(0,49)],51:[(0,39),(46,39),(46,41),(45,41),(45,45),(42,47),(42,51),(40,51),(40,53),(0,53)],53:[(0,38),(44,38),(44,43),(43,46),(41,48),(41,51),(0,51)]}[n]
 ey,ex=np.nonzero(a==7);body_dx=round(43-float(np.median(ex)));a=np.roll(a,body_dx,axis=1)
 mask=Image.new('1',(96,80));ImageDraw.Draw(mask).polygon([(x+body_dx,y+dy) for x,y in polys[n]],fill=1);remove=np.array(mask)
 # Face pixels remain part of the common master, even when the arm passes nearby.
 remove&=a!=7
 common=a.copy();common[remove]=0
 orig=np.array(Image.open(original/f'base_{n+1:03d}.png'));oy,ox=np.nonzero(np.isin(orig,[1,2]));left=ox<ox.min()+2;bb=inv['base_frames'][n+1]['bounds'];muzzle=np.array([int(ox.min()+bb[0]+48),float(np.median(oy[left])+bb[1]+40)])
 dx,sy=[round(v) for v in muzzle-anchor];registered=np.zeros_like(arm);yy,xx=np.nonzero(arm);registered[yy+sy,xx+dx]=arm[yy,xx]
 target=common.copy();target[registered!=0]=registered[registered!=0]
 target[(a!=0)&~remove]=a[(a!=0)&~remove]
 # Hair and facial features occlude the inner upper-arm edge naturally.
 ey,ex=np.nonzero(a==7);face=np.indices(a.shape);protect=(face[0]<=np.median(ey)+2)&(face[1]>=np.median(ex)-2)&(a!=0)
 target[protect]=a[protect]
 # Remove isolated remains of the masked hand, not connected garment pixels.
 seen=set()
 for y,x in zip(*np.nonzero(target)):
  if (y,x) in seen:continue
  component=[];pending=[(int(y),int(x))];seen.add((y,x))
  while pending:
   cy,cx=pending.pop();component.append((cy,cx))
   for ny in range(cy-1,cy+2):
    for nx in range(cx-1,cx+2):
     if 0<=ny<80 and 0<=nx<96 and target[ny,nx] and (ny,nx) not in seen:seen.add((ny,nx));pending.append((ny,nx))
  if len(component)<=3:
   for cy,cx in component:target[cy,cx]=0
 for name,canvas in [('run',a),('common',common),('shoot_body',registered),('gun',np.zeros_like(a)),('shoot',target)]:save_image(canvas.tobytes(),(96,80),art['palette_words'],out/f'{name}_{n:03d}.png')
 arts.append({'frame':n,'image':f'run_{n:03d}.png','landing_dy':dy,'body_dx':body_dx,'generated_frame':n})
 records.append({'run':n,'shoot':n+1,'common_rects':[],'original_muzzle_world':(muzzle-[48,40]).tolist(),'arm_shift':[dx,sy],'body_dx':body_dx,'forward_arm_mask':polys[n],'body_scale':next(r for r in art['frames'] if r['frame']==n)['scale']})
 for row,name in enumerate(('run','shoot')):
  pic=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=(i%6)*288;y=((i//6)*2+row)*264;sheet.paste(pic,(x,y+24),pic);draw.text((x+8,y+4),str(n+row),fill='white')
(out/'pairs.json').write_text(json.dumps({'frames':records,'palette_words':art['palette_words'],'art_approved':False},indent=2));(out/'art.json').write_text(json.dumps({'frames':arts,'palette_words':art['palette_words'],'source_inventory':art['source_inventory']},indent=2));sheet.save(out/'review.png');print(out)
