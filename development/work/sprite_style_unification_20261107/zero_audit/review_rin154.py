"""Native-order comparison with fixed-origin bodies and preserved saber references."""
from pathlib import Path
import sys,json,struct,hashlib,base64
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension';O=D/'ground_remaining154_review';O.mkdir(exist_ok=True)
old=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();new=(D/'prepared_ground_remaining_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(new)=='a8a268fa92912678e70b01b776ffa477dd46c16e791f16f3346c76cd55016319'
tp=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';timeline=json.loads(tp.read_text('utf8'));anims={a['id']:a for a in timeline['animations']}
groups={'run':38,'second':89,'third':90,'first_recovery':88};data={};seen=[];metrics=[]
for name,aid in groups.items():
 seq=anims[aid];data[name]={'native_animation':aid,'sequence':seq,'frames':{}}
 for form,row in [('normal',0),('black',13)]:
  words=struct.unpack_from('<16H',entry(new,9),row*32)
  for typ,arc in [('old',old),('new',new)]:
   frames=[]
   for s in seq['steps']:
    n=s['frame'];p=O/f'{name}_{form}_{typ}_{n:03}.png';rgba(render(arc,0,0,n)[0],words).save(p);frames.append({'frame':n,'position':s['position'],'relative_step':s['relative_step'],'calls':s['duration_calls_uninterrupted'],'event':s['event_bits'],'data':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()})
   data[name]['frames'][form+'_'+typ]=frames
strips={'run':[3,4,7,8,9,10],'second':[83,85,87,89,91,93,95,97],'third':[105,107,109,111,113,115],'recovery':[127,130,131,132,133,134]}
for name,refs in strips.items():
 for form,row in [('normal',0),('black',13)]:
  words=struct.unpack_from('<16H',entry(new,9),row*32);sheet=Image.new('RGB',(192*len(refs),432),'#64717b');dr=ImageDraw.Draw(sheet)
  for col,n in enumerate(refs):
   for line,(arc,label)in enumerate([(old,'old'),(new,'new')]):
    im=rgba(render(arc,0,0,n)[0],words).crop((112,112,208,208)).resize((192,192),Image.Resampling.NEAREST);sheet.paste(im,(col*192,line*216+24),im);dr.text((col*192+4,line*216+4),f'{label} {n}',fill='white')
  p=O/f'{name}_{form}_strip.png';sheet.save(p);seen.append(p.name)
pairs=[(83,84),(85,86),(87,88),(89,90),(91,92),(93,94),(105,106),(107,108)]
for form,row in [('normal',0),('black',13)]:
 words=list(struct.unpack_from('<64H',entry(new,9)));words[:16]=struct.unpack_from('<16H',entry(new,9),row*32)
 for start in(0,4):
  sheet=Image.new('RGB',(1024,304*4),'#64717b');dr=ImageDraw.Draw(sheet)
  for i,(n,e)in enumerate(pairs[start:start+4]):
   effect=render(new,0,0,e)[0];assert np.array_equal(effect,render(old,0,0,e)[0])
   for col,(arc,label)in enumerate([(old,'old'),(new,'new')]):
    body=render(arc,0,0,n)[0]
    for m,a in enumerate((body,np.where(effect,effect,body))):
     im=rgba(a,words).crop((96,112,224,240)).resize((256,256),Image.Resampling.NEAREST);x=col*512+m*256;y=i*304+24;sheet.paste(im,(x,y),im);dr.text((x+4,i*304+4),f'{label} {n}'+(' + '+str(e)if m else''),fill='white')
  p=O/f'effects_{form}_{start//4:02}.png';sheet.save(p);seen.append(p.name)
for n in(147,3,4,7,8,105,107,109,111):
 for label,arc in [('old',old),('new',new)]:
  a=render(arc,0,0,n)[0];yy,xx=np.where((a==15)&(np.indices(a.shape)[0]<155));skin=np.isin(a[130:158,130:175],[12,13,14]);sy,sx=np.where(skin)
  metrics.append({'ref':n,'type':label,'cyan_eye_cells_world':[[int(x-160),int(y-160)]for y,x in zip(yy,xx)],'face_skin_height':int(np.ptp(sy)+1),'face_skin_width':int(np.ptp(sx)+1)})
manifest={'source_sha256':sha(old),'candidate_sha256':sha(new),'timeline_source':str(tp.relative_to(ROOT)),'timeline_sha256':sha(tp.read_bytes()),'origin':[160,160],'groups':data,'sheets':seen,'eye_metrics':metrics,'effect_pairs':pairs,'simulation_only':True,'runtime_verified':False,'limitations':['원표의 순서·상대 분기·유지시간을 사용하며 초당60호출을 가정한다. 외부 입력·상태·이벤트 효과와 물리 좌표는 재현하지 않는다.','검기 합성은 같은 원점의 정적 접점 참고이며 실제 무기 객체의 CLUT·동적 위치·가림과 동일하지 않다.','표의 자기참조는 유지한다. 다시 재생 버튼으로 처음부터 검토할 수 있다.']}
html='''<!doctype html><meta charset="utf-8"><title>린154 순서 검토</title><style>body{background:#222c36;color:white;font:16px sans-serif}canvas{image-rendering:pixelated;background:#64717b}</style><h1>린 지상·이동 진입 비교</h1><p>이전 / 새 그림 · 고정 원점 정수4배 · 원표 유지시간과 상대 분기,60회 호출/초 가정. 입력·물리·검기 객체 미재현.</p><select id="group"><option value="run">이동 진입</option><option value="second">2타</option><option value="third">3타</option><option value="first_recovery">1타·회복</option></select><select id="form"><option value="normal">일반</option><option value="black">레드</option></select><button id="play">처음부터 재생</button><button id="step">다음 표 위치</button><span id="label"></span><br><canvas id="c" width="800" height="416"></canvas><script>const data=DATA,c=document.getElementById('c'),ctx=c.getContext('2d');ctx.imageSmoothingEnabled=false;let at=0,playing=false,next=0;const imgs={};for(const [g,d]of Object.entries(data.groups)){imgs[g]={};for(const [f,arr]of Object.entries(d.frames))imgs[g][f]=arr.map(s=>{const i=new Image();i.src=s.data;return i})}function current(){return data.groups[group.value].frames[form.value+'_new']}function draw(){let s=current()[at];ctx.clearRect(0,0,800,416);for(const [i,k]of ['old','new'].entries())ctx.drawImage(imgs[group.value][form.value+'_'+k][at],112,112,96,96,8+i*400,16,384,384);document.getElementById('label').textContent=s.frame+' / '+s.calls+' calls; event '+s.event}group.onchange=()=>{at=0;playing=false;draw()};form.onchange=draw;play.onclick=()=>{at=0;playing=true;draw();next=performance.now()+current()[at].calls*1000/60};step.onclick=()=>{playing=false;at=(at+1)%current().length;draw()};function tick(t){if(playing&&t>=next){const s=current()[at],pos=s.position+s.relative_step,ni=current().findIndex(v=>v.position===pos);if(ni<0)playing=false;else{at=ni;draw();next=t+current()[at].calls*1000/60}}requestAnimationFrame(tick)}Promise.all(Object.values(imgs).flatMap(g=>Object.values(g)).flat().map(i=>i.decode())).then(()=>{draw();requestAnimationFrame(tick)});</script>'''.replace('DATA',json.dumps(manifest,ensure_ascii=False))
(O/'REVIEW.html').write_text(html,'utf8')
for d in manifest['groups'].values():d.pop('frames')
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sheets':len(seen),'sequences':len(groups)}))
