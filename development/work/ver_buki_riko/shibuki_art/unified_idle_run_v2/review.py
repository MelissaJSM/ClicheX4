from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];work=Path(__file__).parent
old=ROOT/'work/ver_buki_riko/shibuki_art/run_cycle_v3/production';new=work/'production04'
idleold=ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/shibuki_idle000_indexed.png'
idlenew=new/'shibuki_idle000_indexed.png'
art=json.loads((new/'art.json').read_text());metrics=[]
for r in art['frames']:
 n=r['frame'];a=np.array(Image.open(old/f'run_{n:03d}.png'));b=np.array(Image.open(new/f'run_{n:03d}.png'))
 def counts(a):
  dark=a==15;return {'opaque':int((a!=0).sum()),'dark_pixels':int(dark.sum()),'dark_2x2_blocks':int((dark[:-1,:-1]&dark[1:,:-1]&dark[:-1,1:]&dark[1:,1:]).sum())}
 metrics.append({'frame':n,'before':counts(a),'after':counts(b),'native_size':r['native_size'],'ear_to_eye':r['ear_to_eye']})
sheet=Image.new('RGB',(960,400),'#28394b');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
items=[('이전 대기',idleold,(-19,-25)),('이전 이동',old/'run_029.png',(-48,-40)),('수정 대기',idlenew,(-16,-25)),('수정 이동',new/'run_029.png',(-48,-40))]
for i,(title,path,origin) in enumerate(items):
 im=Image.open(path).convert('RGBA');x=i*240;d.text((x+18,12),title,font=font,fill='white')
 for scale,baseline in [(1,120),(4,300)]:
  p=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
  sheet.paste(p,(x+120+origin[0]*scale,baseline+(origin[1]-23)*scale),p)
  d.line((x+12,baseline,x+228,baseline),fill='#627a85')
d.text((18,365),'모두 같은 1배 / 4배율 · 게임 적용용 픽셀의 정적 비교',font=font,fill='white');sheet.save(work/'before_after_1x4x.png')
result={'source':'unified_idle_run_v2/production04','single_scale':art['common_scale'],'per_pose_scaling':False,'idle_native_size':art['idle_size'],'run_metrics':metrics,
        'note':'Dark pixel counts include material shadows and are not a direct contour thickness measurement. Crouched run silhouette height differs with pose.'}
(work/'proportion_metrics.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'before_dark':sum(r['before']['dark_pixels'] for r in metrics),'after_dark':sum(r['after']['dark_pixels'] for r in metrics),'before_2x2':sum(r['before']['dark_2x2_blocks'] for r in metrics),'after_2x2':sum(r['after']['dark_2x2_blocks'] for r in metrics)}))
