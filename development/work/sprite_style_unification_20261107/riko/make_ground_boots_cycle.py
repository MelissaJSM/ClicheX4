"""Read actual sequence bytes and packed pixels for an offline art review."""
from pathlib import Path
import sys,json,hashlib,base64,io
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_sprite_playback import read_disc,parse_sequence,TABLES,at,ZERO_SELECTOR
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
import struct
D=Path(__file__).resolve().parent;O=D/'ground_boots_cycle01';O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_spin_clothes_v1/PL01_U.ARC').read_bytes();new=(D/'prepared_ground_boots_v1/PL01_U.ARC').read_bytes()
assert sha(new)=='55950f7066b5fab6ff8c1c3285b64b530f9cca407d0f0f9027866b31e09bb689'
disc=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin';e=read_disc(disc,['SLUS_005.61'])['SLUS_005.61']
assert sha(e)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'
sequences={str(i):parse_sequence(e,TABLES['zero'],i)for i in(88,89)}
assert all(at(e,ZERO_SELECTOR+int(i),1)==b'\0'for i in sequences)
cases={f'{i} · '+{88:'지상1타',89:'지상2타'}[int(i)]:{'steps':[{'ref':s['frame_ref'],'calls':s['duration_calls']}for s in q['steps']],'loop':q['loop_start_index']}for i,q in sequences.items()}
refs=sorted({s['ref']for c in cases.values()for s in c['steps']});data={};crop=(112,112,208,192)
for name,row in [('normal',0),('black',13)]:
 data[name]={};pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for n in refs:
  uris=[]
  for a in(old,new):
   im=rgba(render(a,0,0,n)[0],pal).crop(crop);buf=io.BytesIO();im.save(buf,format='PNG');uris.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode())
  data[name][str(n)]=uris
 for sequence_id, sequence in sequences.items():
  for start in range(0,len(sequence['steps']),6):
   sheet=Image.new('RGB',(6*288,2*270),'#64717b');draw=ImageDraw.Draw(sheet)
   for j,s in enumerate(sequence['steps'][start:start+6]):
    n=s['frame_ref']
    for side,a in enumerate((old,new)):
     im=rgba(render(a,0,0,n)[0],pal).crop(crop).resize((288,240),Image.Resampling.NEAREST);sheet.paste(im,(j*288,side*270+25),im);draw.text((j*288+4,side*270+4),f'{n:03} / {s["duration_calls"]} calls / '+('before'if side==0 else'candidate'),fill='white')
   sheet.save(O/f'{name}_{sequence_id}_{start:02}.png')
html='''<!doctype html><meta charset="utf-8"><title>리코 지상 공격 부츠 네이티브 비교</title><style>body{font:16px sans-serif;background:#20242a;color:#eee}canvas{background:#64717b;image-rendering:pixelated;border:1px solid #80919b;margin:8px}button,select{font:inherit;margin:8px}small{display:block;max-width:950px;line-height:1.6}</style><h1>리코 지상 공격 부츠 — 이전 / 새 세밀화</h1><small>실제 게임 실행이 아닌 원래 애니메이션 표의 오프라인 재생입니다. 새 ARC에서 직접 복원했습니다. 원점·순서·유지 호출 수·반복 진입점을 보존하며, 60호출/초는 검토용 가정입니다. 입력·물리·효과 이벤트는 실행하지 않습니다.</small><select id="which"></select><select id="palette"><option>normal</option><option>black</option></select><select id="speed"><option value="1">1배</option><option value="0.25" selected>0.25배</option></select><button id="play">일시정지</button><button id="step">한 자세</button><span id="status"></span><h2>1배</h2><canvas id="small0" width="96" height="80"></canvas><canvas id="small1" width="96" height="80"></canvas><h2>최근접 4배</h2><canvas id="big0" width="384" height="320"></canvas><canvas id="big1" width="384" height="320"></canvas><script>const data=DATA,cases=CASES;let frames={},run=true,index=0,elapsed=0,last=0;const names=Object.keys(cases);for(const x of names){let o=document.createElement('option');o.textContent=x;which.append(o)}let selected=cases[names[0]],sequence=selected.steps;const ready=Promise.all(Object.entries(data).map(async([p,refs])=>{frames[p]={};await Promise.all(Object.entries(refs).map(async([k,uris])=>{frames[p][k]=await Promise.all(uris.map(u=>new Promise(r=>{let im=new Image;im.onload=()=>r(im);im.src=u}))) }))}));function draw(){const q=sequence[index];status.textContent='ref '+q.ref+' · '+q.calls+'호출';document.getElementById('status').textContent='ref '+q.ref+' · '+q.calls+'호출';for(let side=0;side<2;side++)for(let prefix of ['small','big']){let c=document.getElementById(prefix+side),x=c.getContext('2d');x.imageSmoothingEnabled=false;x.clearRect(0,0,c.width,c.height);x.drawImage(frames[palette.value][q.ref][side],0,0,c.width,c.height)}}function advance(){index++;if(index>=sequence.length)index=selected.loop;draw()}which.onchange=()=>{selected=cases[which.value];sequence=selected.steps;index=elapsed=0;draw()};palette.onchange=draw;play.onclick=()=>{run=!run;play.textContent=run?'일시정지':'재생'};step.onclick=()=>{run=false;play.textContent='재생';advance()};function tick(t){if(!last)last=t;const dt=Math.min(t-last,250);last=t;if(run){elapsed+=dt*Number(speed.value)*60/1000;while(elapsed>=sequence[index].calls){elapsed-=sequence[index].calls;advance()}}requestAnimationFrame(tick)}ready.then(()=>{draw();requestAnimationFrame(tick)})</script>'''
html=html.replace('DATA',json.dumps(data,separators=(',',':'))).replace('CASES',json.dumps(cases,ensure_ascii=False,separators=(',',':')))
(O/'REVIEW.html').write_text(html,'utf8');(O/'manifest.json').write_text(json.dumps({'before_arc_sha256':sha(old),'after_arc_sha256':sha(new),'exe_sha256':sha(e),'sequences':sequences,'html_sha256':sha(html.encode()),'runtime_verified':False,'clock_assumption':'60 animate calls/sec'},ensure_ascii=False,indent=2),'utf8')
print(O)
