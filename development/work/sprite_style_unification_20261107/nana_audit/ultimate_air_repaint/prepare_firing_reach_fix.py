"""전신 안에서 새 어깨와 실제 총구를 동시에 고정하는 원화 입력. 생성 그림은 아님."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
Y,X=np.indices((384,384));Y-=160;X-=160
a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'firing_reach_fix_inputs_v2';out.mkdir(exist_ok=False)
hands={q['ref']:q['new_hand_bbox']for q in json.loads((D/'canonical_cases_probe_v1/registration.json').read_text('utf8'))['frames']};points={50:{'shoulder':[-2,-3],'elbow':[-11,-2]},52:{'shoulder':[-2,2],'elbow':[-12,3]},54:{'shoulder':[-2,-4],'elbow':[-11,-3]}}
records=[]
for form in ('before','after'):
 board=Image.new('RGBA',(1280,1280));guide=Image.new('RGBA',(1280,1280));gd=ImageDraw.Draw(guide);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',19)
 for i,n in enumerate((50,52,54)):
  source=D/('canonical_cases_probe_v1'if form=='before'else'costume_pair_probe_v2')/f'{form}_{n-1:03}.png';body=np.array(Image.open(source));bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'))
  hx,hy,hx1,hy1=hands[n-1];mask=(X<hx1+1)&(X>=hx-8)&(Y>=hy-3)&(Y<hy1+2);body[mask]=0;body[bar>0]=bar[bar>0]
  if n==54:body[163,154]=0
  Image.fromarray(body).save(out/f'{form}_{n:03}.png');im=a.rgba(body,16 if form=='before'else 0).crop((112,112,208,208)).resize((640,640),Image.Resampling.NEAREST);xy=(i%2*640,i//2*640);board.alpha_composite(im,xy);guide.alpha_composite(im,xy)
  gd=ImageDraw.Draw(guide)
  oy,ox=np.nonzero(bar);muzzle=[int(ox.min())-160,float(np.median(oy[ox==ox.min()]))-160]
  shoulder=points[n]['shoulder'];wrist=[muzzle[0]+8,muzzle[1]+4];elbow=points[n]['elbow']
  def pt(p):return(xy[0]+(p[0]+48)*640/96,xy[1]+(p[1]+48)*640/96)
  gd.line([pt(shoulder),pt(elbow),pt(wrist)],fill=(255,226,0,210),width=3)
  for j,p in enumerate((shoulder,wrist)):
   px,py=pt(p);gd.ellipse((px-5,py-5,px+5,py+5),fill=(255,226,0,255)if j==0 else(0,255,255,255))
  gd.text((xy[0]+45,xy[1]+45),f'{n}: fixed shoulder / fixed pistol',font=font,fill='white')
  if form=='before':records.append({'ref':n,'source_new_body_sha256':digest(source),'muzzle':muzzle,'shoulder_hint':shoulder,'elbow_hint':elbow,'wrist_hint':wrist,'cell':[i%2,i//2],'guidelines_are_annotations_not_pixels':True})
 board.save(out/f'{form}_fixed_body_and_weapon.png');guide.save(out/f'{form}_anchor_guides.png')
write(out/'inputs.json',{'frames':records,'window_world':[-48,-48,48,48],'purpose':'전신·작은 권총·총구는 고정하고 비어 있는 앞팔만 자연스럽게 연결하는 국소 새 원화 입력','images':{p.name:digest(p)for p in out.glob('*.png')},'art_created':False})
