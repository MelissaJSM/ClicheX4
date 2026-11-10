"""Actual packed stills, original body/effect order, and offline review simulation."""
from pathlib import Path
import sys,json,struct,hashlib,base64
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension';O=D/'ground_wall141_review';O.mkdir(exist_ok=True)
old=(D/'prepared_ground_first_v1/PL01_U.ARC').read_bytes();new=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(new)=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
timeline_path=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';timeline=json.loads(timeline_path.read_text('utf8'));groups={'ground':(0,88,112),'wall':(1,94,118)}
proposal=json.loads((D/'prepared_ground_wall_v1/proposal.json').read_text('utf8'));keys=[(int(k[1]),int(k[3:]))for k in proposal['new_art_refs']];head=[]
for n,eye_y in [(147,146),(71,148),(73,148)]:
 for label,arc in [('old',old)]+([]if n==147 else [('new',new)]):
  a=render(arc,0,0,n)[0];region=a[132:eye_y,130:170];y,x=np.where(region>0);width=max(int(np.ptp(np.where(row>0)[0])+1)for row in region if np.any(row));eye=np.argwhere((a==15)&(np.indices(a.shape)[0]<154))
  skin=np.isin(a[135:153,130:163],[12,13,14]);sy,sx=np.where(skin)
  head.append({'ref':n,'form':label,'upper_head_band_world_y':[132-160,eye_y-160],'upper_head_max_row_width':width,'top_to_eye_row':int(eye_y-(y.min()+132)),'native_cyan_eye_cells':[[int(xx-160),int(yy-160)]for yy,xx in eye],'face_skin_bbox_width':int(np.ptp(sx)+1),'face_skin_bbox_height':int(np.ptp(sy)+1),'old_eye_row_is_visually_selected':label=='old'and n!=147,'band_excludes_lower_trailing_hair_but_includes_bonnet':True})
for start in range(0,len(keys),4):
 subset=keys[start:start+4];sheet=Image.new('RGB',(1152,312*len(subset)),'#64717b');dr=ImageDraw.Draw(sheet)
 for row,(b,n)in enumerate(subset):
  for col,(form,pi,arc)in enumerate([('normal old',0,old),('normal new',0,new),('red old',13,old),('red new',13,new)]):
   words=struct.unpack_from('<16H',entry(new,9),pi*32);im=rgba(render(arc,b,b*5,n)[0],words).crop((112,112,208,208)).resize((288,288),Image.Resampling.NEAREST);sheet.paste(im,(col*288,row*312+24),im);dr.text((col*288+3,row*312+4),f'b{b}:{n} {form}',fill='white')
 sheet.save(O/f'readback_{start//4:02}.png')
manifest={'candidate_sha256':sha(new),'parent_sha256':sha(old),'origin':[160,160],'timeline_source':str(timeline_path.relative_to(ROOT)),'timeline_sha256':sha(timeline_path.read_bytes()),'head_metrics':head,'runtime_verified':False,'simulation_only':True,'limitations':['원래 표의 순서·유지시간을60회 호출/초 가정으로 재생한다.','표 끝의 자동 반복은 검토용이며 게임 상태전이·입력·검기 객체 위치/가림을 재현하지 않는다.','검기 합성은 같은 원점 정적 접점 참고다. 실제 무기 객체의 동적 CLUT·위치를 재현하지 않는다.'],'groups':{}}
pairs={'ground':[(71,72),(73,74),(75,76),(77,78),(79,80),(81,80)],'wall':[(51,52),(54,55),(57,58),(59,60),(61,62),(63,64),(65,64)]}
for group,(b,body_id,effect_id)in groups.items():
 seq=next(a for a in timeline['animations']if a['id']==body_id);fx=next(a for a in timeline['animations']if a['id']==effect_id);data={'bank':b,'body_animation':body_id,'effect_animation':effect_id,'body_sequence':seq,'effect_sequence':fx,'frames':{}}
 for form,row in [('normal',0),('black',13)]:
  words=list(struct.unpack_from('<64H',entry(new,9)));words[:16]=struct.unpack_from('<16H',entry(new,9),row*32)
  for typ,arc in [('old',old),('new',new)]:
   frames=[]
   for s in seq['steps']:
    n=s['frame'];p=O/f'{group}_{form}_{typ}_{n:03}.png';rgba(render(arc,b,b*5,n)[0],words).save(p);frames.append({'frame':n,'calls':s['duration_calls_uninterrupted'],'data':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()})
   data['frames'][form+'_'+typ]=frames
  for start in range(0,len(pairs[group]),3):
   pairs_page=pairs[group][start:start+3];sheet=Image.new('RGB',(1280,352*len(pairs_page)),'#64717b');dr=ImageDraw.Draw(sheet)
   for i,(n,e)in enumerate(pairs_page):
    for k,arc in enumerate((old,new)):
     body=render(arc,b,b*5,n)[0];effect=render(arc,b,b*5,e)[0];comp=np.where(effect,effect,body)
     for mode,a in enumerate((body,comp)):
      x=(k*2+mode)*320;im=rgba(a,words).crop((88,112,216,216)).resize((256,208),Image.Resampling.NEAREST);sheet.paste(im,(x+32,i*352+64),im);dr.text((x+4,i*352+8),f'{n}+{e} '+('old'if k==0 else'new')+(' body'if mode==0 else' effect'),fill='white')
   sheet.save(O/f'{group}_{form}_effects_{start//3:02}.png')
 manifest['groups'][group]=data
html='''<!doctype html><meta charset="utf-8"><title>린141 연속 검토</title><style>body{background:#222c36;color:white;font:16px sans-serif}canvas{image-rendering:pixelated;background:#64717b}</style><h1>린 지상 후속·벽 공격 연속 비교</h1><p>왼쪽 이전 / 오른쪽 새 그림 · 고정 원점 · 정수4배 · 원래 표 유지시간,60회 호출/초 가정.검기 객체/판정/외부 입력 미재현.끝 반복은 검토용.</p><select id="group"><option value="ground">지상 첫타</option><option value="wall">벽 공격</option></select><select id="form"><option value="normal">일반</option><option value="black">레드</option></select><button id="play">재생</button><button id="step">다음</button><span id="label"></span><br><canvas id="c" width="800" height="416"></canvas><script>const data=DATA,c=document.getElementById('c'),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;let at=0,playing=false,next=0;const imgs={};for(const [g,d]of Object.entries(data.groups)){imgs[g]={};for(const [f,arr]of Object.entries(d.frames))imgs[g][f]=arr.map(s=>{const i=new Image();i.src=s.data;return i})}function current(){return data.groups[group.value].frames[form.value+'_new']}function draw(){let s=current()[at];ctx.clearRect(0,0,800,416);for(const [i,k]of ['old','new'].entries())ctx.drawImage(imgs[group.value][form.value+'_'+k][at],112,112,96,96,8+i*400,16,384,384);document.getElementById('label').textContent=s.frame+' / '+s.calls+' calls'}group.onchange=()=>{at=0;draw()};form.onchange=draw;play.onclick=()=>{playing=!playing;next=performance.now()};step.onclick=()=>{playing=false;at=(at+1)%current().length;draw()};function tick(t){if(playing&&t>=next){let s=current()[at];draw();next=t+s.calls*1000/60;at=(at+1)%current().length}requestAnimationFrame(tick)}Promise.all(Object.values(imgs).flatMap(g=>Object.values(g)).flat().map(i=>i.decode())).then(()=>{draw();requestAnimationFrame(tick)});</script>'''.replace('DATA',json.dumps(manifest,ensure_ascii=False))
(O/'REVIEW.html').write_text(html,'utf8')
for d in manifest['groups'].values():d.pop('frames')
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'out':str(O),'head_metrics':head},ensure_ascii=False))
