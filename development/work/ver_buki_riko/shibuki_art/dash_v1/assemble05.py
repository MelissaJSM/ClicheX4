"""대시 몸과 기존 버스터 팔을 결합한다. 총구는 원본 프레임에 등록한다."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent;src=d/'normalized03';out=d/'production05';out.mkdir(exist_ok=True)
art=json.loads((src/'art.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text());original=ROOT/Path(art['source_inventory']).parent
arm=np.array(Image.open(d.parent/'standing_buster_v1/production03/registered_arm_085.png'));arm[40:]=0
yy,xx=np.nonzero(arm==4);anchor=np.array([int(xx.min()),float(np.median(yy[xx==xx.min()]))])
polys={67:[(0,38),(39,38),(41,40),(41,45),(40,49),(0,49)],69:[(0,43),(32,43),(35,45),(36,48),(36,53),(0,53)],
71:[(0,50),(29,50),(32,53),(32,59),(0,59)],75:[(0,50),(29,50),(32,53),(32,59),(0,59)],
77:[(0,42),(37,42),(39,44),(40,47),(38,51),(0,51)],79:[(0,38),(41,38),(43,42),(42,47),(0,47)],
81:[(0,40),(40,40),(41,43),(41,47),(39,50),(0,50)],83:[(0,35),(39,35),(41,38),(41,43),(40,46),(0,46)]}
sheet=Image.new('RGB',(4*288,4*264),'#28394b');draw=ImageDraw.Draw(sheet);records=[]
for i,r in enumerate(art['frames']):
    n=r['frame'];a=np.array(Image.open(src/r['image']));mask=Image.new('1',(96,80));ImageDraw.Draw(mask).polygon(polys[n],fill=1);remove=np.array(mask);remove&=a!=7
    common=a.copy();common[remove]=0
    orig=np.array(Image.open(original/f'base_{n+1:03d}.png'));oy,ox=np.nonzero(np.isin(orig,[1,2]));left=ox<ox.min()+2;bb=inv['base_frames'][n+1]['bounds'];muzzle=np.array([int(ox.min()+bb[0]+48),float(np.median(oy[left])+bb[1]+40)])
    dx,dy=[round(v) for v in muzzle-anchor];registered=np.zeros_like(arm);yy,xx=np.nonzero(arm);registered[yy+dy,xx+dx]=arm[yy,xx]
    target=common.copy();target[registered!=0]=registered[registered!=0];target[(a!=0)&~remove]=a[(a!=0)&~remove]
    ey,ex=np.nonzero(a==7);grid=np.indices(a.shape);protect=(grid[0]<=np.median(ey)+2)&(grid[1]>=np.median(ex)-2)&(a!=0);target[protect]=a[protect]
    for name,canvas in [('run',a),('common',common),('shoot_body',registered),('gun',np.zeros_like(a)),('shoot',target)]:save_image(canvas.tobytes(),(96,80),art['palette_words'],out/f'{name}_{n:03d}.png')
    records.append({'run':n,'shoot':n+1,'common_rects':[],'original_muzzle_world':(muzzle-[48,40]).tolist(),'arm_shift':[dx,dy],'forward_arm_mask':polys[n],'body_scale':r['scale']})
    for row,name in enumerate(('run','shoot')):
        im=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);x=(i%4)*288;y=(i//4*2+row)*264;sheet.paste(im,(x,y+24),im);draw.text((x+8,y+5),str(n+row),fill='white')
(out/'art.json').write_text(json.dumps(art,indent=2));(out/'pairs.json').write_text(json.dumps({'frames':records,'palette_words':art['palette_words'],'art_approved':False},indent=2));sheet.save(out/'review.png');print(out)
