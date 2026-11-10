from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent;body=d/'production02';shot_source=ROOT/'work/ver_buki_riko/shibuki_art/unified_idle_run_v3/shoot_raised_normalized'
art=json.loads((body/'art.json').read_text());source=json.loads((shot_source/'art.json').read_text());out=d/'paired';out.mkdir(exist_ok=False)
sheet=Image.new('RGB',(2048,1024),'#28394b');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16);records=[]
for i,r in enumerate(art['frames']):
 n=r['frame'];a=np.array(Image.open(body/r['image']));s=next(s for s in source['frames'] if s['run']==n);b=np.array(Image.open(shot_source/s['image']))
 eye_mask=a==7;eye_mask[40:]=False;ey,ex=np.nonzero(eye_mask);eye_x=float(np.median(ex));eye_y=float(np.median(ey));ax=int(np.nonzero(a)[1].min());ay=round(eye_y)
 delta=[round(s['original_muzzle'][j]-s['generated_muzzle'][j]) for j in (0,1)];shifted=np.zeros_like(b);yy,xx=np.nonzero(b);shifted[yy+delta[1],xx+delta[0]]=b[yy,xx]
 mx,my=s['original_muzzle'];gx,gy=int(mx)+47,round(my)+36
 common=a.copy();common[ay:ay+16,ax:ax+16]=0;arm=np.zeros_like(a);arm[ay:ay+16,ax:ax+16]=shifted[ay:ay+16,ax:ax+16]
 for y in range(ay,ay+16):
  for x in range(ax,ax+16):
   if (y<=eye_y+2 and x>=eye_x-2) or y>=eye_y+8:arm[y,x]=a[y,x]
 gun=np.zeros_like(a);gun[gy:gy+16,gx:gx+16]=shifted[gy:gy+16,gx:gx+16]
 for y in range(gy,gy+16):
  for x in range(gx,gx+16):
   if (y<=eye_y+2 and x>=eye_x-2) or y>=eye_y+8:gun[y,x]=0
 target=common.copy();target[arm!=0]=arm[arm!=0];target[gun!=0]=gun[gun!=0]
 for name,canvas in [('run',a),('common',common),('shoot_body',arm),('gun',gun),('shoot',target)]:save_image(canvas.tobytes(),(96,80),art['palette_words'],out/f'{name}_{n:03d}.png')
 records.append({'run':n,'shoot':n+1,'common_rects':[],'run_arm_rect':[ax,ay],'gun_rect':[gx,gy],'original_muzzle':s['original_muzzle'],'muzzle_shift':delta})
 for row,name in enumerate(('run','shoot')):
  pic=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);bx=(i%8)*256;by=((i//8)*2+row)*256;sheet.paste(pic,(bx-16,by+16),pic);draw.text((bx+5,by+3),f'{name} {n if row==0 else n+1:03d}',font=font,fill='white')
(out/'pairs.json').write_text(json.dumps({'frames':records,'palette_words':art['palette_words'],'art_approved':False},indent=2));sheet.save(out/'paired_master_3x.png');print(out)
