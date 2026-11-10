from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
work=Path(__file__).parent;body=work/'paired_body';shoot=ROOT/'work/ver_buki_riko/shibuki_art/unified_idle_run_v3/shoot_raised_normalized'
art=json.loads((body/'art.json').read_text());shot=json.loads((shoot/'art.json').read_text());layouts=json.loads((work/'joint_layout.json').read_text())
out=work/'paired';out.mkdir(exist_ok=False);records=[];sheet=Image.new('RGB',(8*256,4*256),'#28394b');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
for i,r in enumerate(art['frames']):
 n=r['frame'];a=np.array(Image.open(body/r['image']));s=next(s for s in shot['frames'] if s['run']==n);b=np.array(Image.open(shoot/s['image']))
 layout=next(l for l in layouts if l['frame']==n)
 if not layout['fits']:raise ValueError(f'Unpacked body {n}')
 rects=layout['rects'];ey,ex=np.nonzero(a==7);eye_x=float(np.median(ex));eye_y=float(np.median(ey))
 # Select the existing tile covering the front forearm and chest. All other
 # rectangles remain shared, and all pixels outside this window are retained.
 def score(rect):
  x,y=rect;return abs(x-(eye_x-5))+1.7*abs(y-(eye_y+4))
 ax,ay=layout['arm_rect']
 delta=[round(s['original_muzzle'][j]-s['generated_muzzle'][j]) for j in (0,1)]
 shifted=np.zeros_like(b);yy,xx=np.nonzero(b);yy=yy+delta[1];xx=xx+delta[0]
 if np.any((xx<0)|(xx>=96)|(yy<0)|(yy>=80)):raise ValueError('Translated arm outside canvas')
 shifted[yy,xx]=b[np.nonzero(b)]
 mx,my=s['original_muzzle'];gx,gy=int(mx)+48-1,round(my)+40-4
 common=a.copy();common[ay:ay+16,ax:ax+16]=0
 arm=np.zeros_like(a);arm[ay:ay+16,ax:ax+16]=shifted[ay:ay+16,ax:ax+16]
 # Keep the face and a two-row lower attachment boundary from the body sheet.
 for y in range(ay,ay+16):
  for x in range(ax,ax+16):
   if (y<=eye_y+2 and x>=eye_x-2) or y>=eye_y+8:arm[y,x]=a[y,x]
 gun=np.zeros_like(a);gun[gy:gy+16,gx:gx+16]=shifted[gy:gy+16,gx:gx+16]
 # The gun layer may cover hair in front, but must not duplicate the face.
 for y in range(gy,gy+16):
  for x in range(gx,gx+16):
   if (y<=eye_y+2 and x>=eye_x-2) or y>=eye_y+8:gun[y,x]=0
 target=common.copy();target[arm!=0]=arm[arm!=0];target[gun!=0]=gun[gun!=0]
 for name,data in [('common',common),('shoot_body',arm),('gun',gun),('shoot',target),('run',a)]:save_image(data.tobytes(),(96,80),art['palette_words'],out/f'{name}_{n:03d}.png')
 record={'run':n,'shoot':n+1,'common_rects':rects,'run_arm_rect':[ax,ay],'shoot_arm_rect':[ax,ay],'gun_rect':[gx,gy],
         'muzzle_shift':delta,'original_muzzle':s['original_muzzle'],'body_art':r['image']};records.append(record)
 for row,(name,data) in enumerate([('run',a),('shoot',target)]):
  pos=(i//8)*2+row;bx,by=(i%8)*256,pos*256;pic=Image.open(out/f'{name}_{n:03d}.png').convert('RGBA').resize((288,240),Image.Resampling.NEAREST);sheet.paste(pic,(bx-16,by+16),pic);draw.text((bx+5,by+3),f'{name} {n if row==0 else n+1:03d}',font=font,fill='white')
sheet.save(out/'paired_master_3x.png');(out/'pairs.json').write_text(json.dumps({'frames':records,'palette_words':art['palette_words'],'art_approved':False},indent=2)+'\n')
print(json.dumps({'out':str(out),'arms':[(r['run'],r['run_arm_rect'],r['gun_rect']) for r in records]}))
