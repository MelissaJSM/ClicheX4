"""Same-origin contact sheets and body timeline; these are not runtime captures."""
from pathlib import Path
import sys,json,struct,hashlib,base64
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension';O=D/'ground122_contact_review';O.mkdir(exist_ok=True)
old=(D/'prepared_hurt_lowhp_v1/PL01_U.ARC').read_bytes();new=(D/'prepared_ground_first_v1/PL01_U.ARC').read_bytes()
timeline=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json').read_text('utf8'))
seq=next(a for a in timeline['animations']if a['id']==88);refs=[61,62,63,65,67,69,71,73,75,77,79,81,82,131,132,133,134]
manifest={'same_world_origin':[160,160],'native_body_animation':88,'native_effect_animation':112,'body_frames':refs,'pair_preview':[[63,64],[65,66],[67,68],[69,70]],'runtime_verified':False,'pairs_are_same_origin_static_preview':True,'timing_assumption':'60呼出/秒の表示シミュレーション。外部入力・当たり判定・武器位置・終了状態は未再現。'}
for label,row in(('normal',0),('black',13)):
 words=list(struct.unpack_from('<64H',entry(new,9)));words[:16]=struct.unpack_from('<16H',entry(new,9),row*32)
 sheet=Image.new('RGB',(1280,4*424),'#64717b');draw=ImageDraw.Draw(sheet)
 for i,(n,e)in enumerate(manifest['pair_preview']):
  for k,arc in enumerate((old,new)):
   body=render(arc,0,0,n)[0];fx=render(arc,0,0,e)[0];comp=np.where(fx>0,fx,body)
   for mode,a in enumerate((body,comp)):
    x=(k*2+mode)*320;y=i*424;im=rgba(a,words).crop((88,112,216,192)).resize((640,400),Image.Resampling.NEAREST)
    # Full128px canvas at2x is kept in320px cell: no clipped saber.
    im=rgba(a,words).crop((88,112,216,208)).resize((256,192),Image.Resampling.NEAREST)
    sheet.paste(im,(x+32,y+100),im);draw.text((x+5,y+5),f'{n}+{e} '+('old'if k==0 else'new')+(' body'if mode==0 else' same-origin effect'),fill='white')
 sheet.save(O/f'{label}_effects.png')
 for start in range(0,len(refs),6):
  part=refs[start:start+6];page=Image.new('RGB',(6*320,2*344),'#64717b');d=ImageDraw.Draw(page)
  for i,n in enumerate(part):
   for iy,arc in enumerate((old,new)):
    im=rgba(render(arc,0,0,n)[0],words).crop((120,112,200,192)).resize((320,320),Image.Resampling.NEAREST);page.paste(im,(i*320,iy*344+24),im);d.text((i*320+4,iy*344+4),str(n)+(' old'if iy==0 else' new'),fill='white')
  page.save(O/f'{label}_sequence_{start//6:02}.png')
 frames=[]
 for s in seq['steps']:
  n=s['frame'];p=O/f'{label}_{n:03}.png';rgba(render(new,0,0,n)[0],words).save(p)
  frames.append({'frame':n,'calls':s['duration_calls_uninterrupted'],'data':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()})
 manifest[label+'_frames']=frames
manifest['timing_assumption']='60회 호출/초를 가정한 몸체 순서 미리보기. 외부 입력·판정·검기 객체 위치·종료 상태는 재현하지 않는다.'
data=json.dumps(manifest,ensure_ascii=False)
html='''<!doctype html><meta charset="utf-8"><title>린 첫타 접점 검토</title><style>body{background:#222c36;color:white;font:16px sans-serif}canvas{image-rendering:pixelated;background:#64717b}</style><h1>린 첫타 몸체 순서</h1><p>고정 원점 · 원래 유지시간, 60회 호출/초 가정 · 검기 객체/판정/외부 입력 미재현.71 이후 일부 자세는 후속 미술 작업 대상.</p><select id="form"><option value="normal">일반</option><option value="black">레드</option></select><button id="play">재생</button><button id="step">다음</button><span id="name"></span><br><canvas id="c" width="640" height="640"></canvas><script>const d=DATA;const c=document.getElementById('c'),x=c.getContext('2d');x.imageSmoothingEnabled=false;let at=0,playing=false,next=0;const imgs={};for(const f of ['normal','black'])imgs[f]=d[f+'_frames'].map(s=>{let i=new Image();i.src=s.data;return i});function draw(){let f=form.value,s=d[f+'_frames'][at];x.clearRect(0,0,640,640);x.drawImage(imgs[f][at],112,112,96,96,32,32,576,576);name.textContent=s.frame+' / '+s.calls+' calls'};document.getElementById('name');document.getElementById('play').onclick=()=>{playing=!playing;next=performance.now();};step.onclick=()=>{playing=false;at=(at+1)%d[form.value+'_frames'].length;draw()};form.onchange=draw;function tick(t){if(playing&&t>=next){let s=d[form.value+'_frames'][at];next=t+s.calls*1000/60;draw();at=(at+1)%d[form.value+'_frames'].length}requestAnimationFrame(tick)};Promise.all(Object.values(imgs).flat().map(i=>i.decode())).then(()=>{draw();requestAnimationFrame(tick)});</script>'''.replace('DATA',data).replace("name.textContent", "document.getElementById('name').textContent")
(O/'REVIEW.html').write_text(html,'utf8')
manifest.pop('normal_frames');manifest.pop('black_frames');(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
print(str(O))
