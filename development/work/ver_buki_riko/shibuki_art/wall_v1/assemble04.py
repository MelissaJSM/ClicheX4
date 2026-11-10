"""일반 벽 자세와 같은 몸에 기존 버스터 팔을 원본 총구로 등록한다."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent;src=d/'normalized05';out=d/'production04';assert not (out/'art.json').exists();out.mkdir(exist_ok=True)
art=json.loads((src/'art.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text());original=ROOT/Path(art['source_inventory']).parent
arm=np.array(Image.open(d.parent/'standing_buster_v1/production03/registered_arm_085.png'));arm[40:]=0
yy,xx=np.nonzero(arm==4);anchor=np.array([int(xx.min()),float(np.median(yy[xx==xx.min()]))])
polys={55:[(0,34),(38,34),(41,39),(42,41),(40,44),(0,44)],57:[(0,35),(40,35),(43,39),(42,43),(0,43)],59:[(0,31),(38,31),(40,35),(42,39),(40,43),(0,43)],61:[(0,35),(39,35),(41,39),(43,43),(40,46),(0,46)],63:[(0,36),(41,36),(44,40),(45,44),(42,48),(0,48)],65:[(0,36),(39,36),(42,41),(42,44),(40,47),(0,47)]}
sheet=Image.new('RGB',(7*288,2*264),'#28394b');draw=ImageDraw.Draw(sheet);records=[]
for i,r in enumerate(art['frames']):
 n=r['frame'];a=np.array(Image.open(src/r['image']));mask=Image.new('1',(96,80));ImageDraw.Draw(mask).polygon(polys[n],fill=1);remove=np.array(mask);remove&=a!=7;ey,ex=np.nonzero(a==7);gy,gx=np.indices(a.shape);remove&=~((gy<=np.median(ey)+3)&(gx>=np.median(ex)-5)&(a!=0));common=a.copy();common[remove]=0
 orig=np.array(Image.open(original/f'base_{n+1:03d}.png'));oy,ox=np.nonzero(np.isin(orig,[1,2]));edge=ox<ox.min()+2;bb=inv['base_frames'][n+1]['bounds'];muzzle=np.array([int(ox.min()+bb[0]+48),float(np.median(oy[edge])+bb[1]+40)])
 dx,dy=[round(v) for v in muzzle-anchor];registered=np.zeros_like(arm);yy,xx=np.nonzero(arm);assert (yy+dy).min()>=0 and (xx+dx).min()>=0;registered[yy+dy,xx+dx]=arm[yy,xx]
 target=common.copy();target[registered!=0]=registered[registered!=0];target[(a!=0)&~remove]=a[(a!=0)&~remove]
 ey,ex=np.nonzero(a==7);grid=np.indices(a.shape);protect=(grid[0]<=np.median(ey)+2)&(grid[1]>=np.median(ex)-2)&(a!=0);target[protect]=a[protect]
 for name,canvas in [('run',a),('common',common),('shoot_body',registered),('gun',np.zeros_like(a)),('shoot',target)]:save_image(canvas.tobytes(),(96,80),art['palette_words'],out/f'{name}_{n:03d}.png')
 records.append({'run':n,'shoot':n+1,'common_rects':[],'original_muzzle_world':(muzzle-[48,40]).tolist(),'arm_shift':[dx,dy],'forward_arm_mask':polys[n],'body_scale':r['scale']})
 for row,name in enumerate(('run','shoot')):
  im=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,((i+1)*288,row*264+24),im);draw.text(((i+1)*288+8,row*264+5),str(n+row),fill='white')
for row in range(2):
 im=Image.open(d.parent/'standing_buster_v1/parent_000.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(0,row*264+24),im);draw.text((8,row*264+5),'ACCEPTED IDLE',fill='white')
(out/'art.json').write_text(json.dumps(art,indent=2));(out/'pairs.json').write_text(json.dumps({'frames':records,'palette_words':art['palette_words'],'art_approved':False},indent=2));sheet.save(out/'review.png');print(out)
