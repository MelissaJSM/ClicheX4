"""원표 순서·고정 원점과 검기 자원을 비교하는 정적 검토 산출물."""
from pathlib import Path
import sys,json,struct,hashlib,base64
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension';O=D/'dash_saber222_review';O.mkdir(exist_ok=True)
old=(D/'prepared_ladder_dash01/PL01_U.ARC').read_bytes();new=(D/'prepared_dash_saber01/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(new)=='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da'
tp=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json';anims={a['id']:a for a in json.loads(tp.read_text('utf8'))['animations']}
groups={'ground_dash_saber':(104,'Ground dash saber native 104')};data={};sheets=[]
def bounds(arrays):
 boxes=[Image.fromarray(np.uint8(a>0)*255).getbbox()for a in arrays];boxes=[b for b in boxes if b]
 return (min([160]+[b[0]for b in boxes])-3,min([160]+[b[1]for b in boxes])-3,max([160]+[b[2]for b in boxes])+3,max([160]+[b[3]for b in boxes])+3)
for name,(aid,label)in groups.items():
 seq=anims[aid];gb=seq['graphics_bank'];refs=list(dict.fromkeys(s['frame']for s in seq['steps']));box=bounds([render(arc,gb,gb*5,n)[0]for arc in(old,new)for n in refs]);data[name]={'label':label,'native_animation':aid,'sequence':seq,'crop':box,'frames':{}}
 for form,row in [('normal',0),('black',13)]:
  words=list(struct.unpack_from('<64H',entry(new,9)));words[:16]=struct.unpack_from('<16H',entry(new,9),row*32)
  for typ,arc in [('old',old),('new',new)]:
   frames=[]
   for s in seq['steps']:
    n=s['frame'];p=O/f'{name}_{form}_{typ}_{n:03}.png';rgba(render(arc,gb,gb*5,n)[0],words).save(p);frames.append({'frame':n,'position':s['position'],'relative_step':s['relative_step'],'calls':s['duration_calls_uninterrupted'],'event':s['event_bits'],'data':'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()})
   data[name]['frames'][form+'_'+typ]=frames
  w,h=(box[2]-box[0])*2,(box[3]-box[1])*2;sheet=Image.new('RGB',((w+8)*len(refs),(h+26)*2),'#64717b');dr=ImageDraw.Draw(sheet)
  for col,n in enumerate(refs):
   for line,(arc,label2)in enumerate([(old,'old'),(new,'new')]):
    im=rgba(render(arc,gb,gb*5,n)[0],words).crop(box).resize((w,h),Image.Resampling.NEAREST);sheet.paste(im,(col*(w+8),line*(h+26)+24),im);dr.text((col*(w+8)+2,line*(h+26)+4),f'{label2} b{gb} {n}',fill='white')
  p=O/f'{name}_{form}_strip.png';sheet.save(p);sheets.append(p.name)
pairs=[]
manifest={'source_sha256':sha(old),'candidate_sha256':sha(new),'timeline_source':str(tp.relative_to(ROOT)),'timeline_sha256':sha(tp.read_bytes()),'origin':[160,160],'groups':data,'sheets':sheets,'effect_pairs':pairs,'simulation_only':True,'runtime_verified':False,'limitations':['원표의 순서·상대 분기·유지시간을 사용하며 초당60호출을 가정한다. 외부 입력·상태·이벤트 효과와 물리 좌표는 재현하지 않는다.','검기 합성은 같은 원점의 정적 접점 참고이며 실제 무기 객체의 CLUT·동적 위치·가림과 동일하지 않다.','사다리 베기·질풍아 표는 원래 몸/이펙트 자원 참조를 나열한다. 부분 타일 갱신과 별도 객체의 실제 화면 합성을 구현한 것이 아니다.','표의 자기참조는 유지한다. 재생 버튼으로 처음부터 검토할 수 있다.']}
html='''<!doctype html><meta charset="utf-8"><title>린222 원순서 검토</title><style>body{background:#222c36;color:white;font:16px sans-serif}canvas{image-rendering:pixelated;background:#64717b}</style><h1>린 사다리 베기·질풍아 준비 비교</h1><p>이전 / 새 그림 · 고정 원점 정수4배 · 원표 유지시간과 상대 분기,60회 호출/초 가정. 입력·물리·검기 객체 미재현.</p><select id="group"></select><select id="form"><option value="normal">일반</option><option value="black">레드</option></select><button id="play">처음부터 재생</button><button id="step">다음 표 위치</button><span id="label"></span><br><canvas id="c"></canvas><script>const data=DATA,c=document.getElementById('c'),ctx=c.getContext('2d');let at=0,playing=false,next=0;const imgs={};for(const [g,d]of Object.entries(data.groups)){group.add(new Option(d.label,g));imgs[g]={};for(const [f,arr]of Object.entries(d.frames))imgs[g][f]=arr.map(s=>{const i=new Image();i.src=s.data;return i})}function current(){return data.groups[group.value].frames[form.value+'_new']}function draw(){let s=current()[at],b=data.groups[group.value].crop,w=(b[2]-b[0])*4,h=(b[3]-b[1])*4;c.width=2*(w+16);c.height=h+32;ctx.imageSmoothingEnabled=false;for(const [i,k]of ['old','new'].entries())ctx.drawImage(imgs[group.value][form.value+'_'+k][at],b[0],b[1],b[2]-b[0],b[3]-b[1],8+i*(w+16),16,w,h);document.getElementById('label').textContent=s.frame+' / '+s.calls+' calls; event '+s.event}group.onchange=()=>{at=0;playing=false;draw()};form.onchange=draw;play.onclick=()=>{at=0;playing=true;draw();next=performance.now()+current()[at].calls*1000/60};step.onclick=()=>{playing=false;at=(at+1)%current().length;draw()};function tick(t){if(playing&&t>=next){const s=current()[at],pos=s.position+s.relative_step,ni=current().findIndex(v=>v.position===pos);if(ni<0)playing=false;else{at=ni;draw();next=t+current()[at].calls*1000/60}}requestAnimationFrame(tick)}Promise.all(Object.values(imgs).flatMap(g=>Object.values(g)).flat().map(i=>i.decode())).then(()=>{draw();requestAnimationFrame(tick)});</script>'''.replace('DATA',json.dumps(manifest,ensure_ascii=False))
(O/'REVIEW.html').write_text(html,'utf8')
for d in manifest['groups'].values():d.pop('frames')
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sheets':len(sheets),'sequences':len(groups)}))
