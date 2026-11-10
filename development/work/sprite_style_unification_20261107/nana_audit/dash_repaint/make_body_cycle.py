"""대시 기본형 후보를 실제 크기 및 확대 연속 재생으로 비교하는 로컬 검토물."""
from pathlib import Path
import sys,json,base64,io
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from prepare_next_guides import body_path
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());need(sha(a.data)==p['parent_arc_sha256'],'Parent');out=D/'body_cycle_v1';need(not out.exists(),'Fresh output');out.mkdir();data={};reports=[]
    for n in(0,67,69,71,73,75,77,79,81,83,93,94):
        old=a.composite(n)[0]
        if n==0:new=old
        elif n==73:
            ar=np.array(Image.open(body_path(71)));fx=np.array(Image.open(D/'effects/effect_073.png'));ar=np.where(fx,fx,ar).astype(np.uint8);new=a.rgba(ar)
        else:new=a.rgba(np.array(Image.open(body_path(n))))
        images=[]
        for im in(old,new):
            buf=io.BytesIO();im.crop((112,120,208,192)).save(buf,format='PNG');images.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode('ascii'))
        data[str(n)]=images;reports.append({'ref':n,'old_rgba_sha256':sha(np.asarray(old).tobytes()),'new_rgba_sha256':sha(np.asarray(new).tobytes())})
    animations={str(q['id']):[{'ref':s['frame_ref'],'calls':s['duration_calls']}for s in q['steps']]for q in p['animations']if q['id']in(16,17,18,19)}
    cases={'대시 반복71/75/73':[{'ref':71,'calls':1},{'ref':75,'calls':1},{'ref':73,'calls':1}],
           '대시 종료77→83':[s for s in animations['17'][:4]]+[{'ref':0,'calls':18}],
           '시작67→반복':[s for s in animations['16'][2:8]]+[{'ref':71,'calls':1},{'ref':75,'calls':1},{'ref':73,'calls':1}],
           '공중 대시93/94':animations['18'][:3]+[{'ref':71,'calls':1},{'ref':75,'calls':1},{'ref':73,'calls':1}]}
    html='''<!doctype html><meta charset="utf-8"><title>나나 기본 대시 후보 연결 검토</title><style>body{font:16px sans-serif;background:#20242a;color:#eee}canvas{background:#b6c0c7;image-rendering:pixelated;border:1px solid #61717b;margin-right:20px}section{display:flex;gap:24px}button,select{font:inherit;margin:8px}small{display:block;max-width:950px;line-height:1.6}h2{font-size:18px}</style><h1>나나 기본 대시 후보: 이전 / 새 원화</h1><small>실제 게임 실행이 아닌 정적 원화 재생입니다. 원 애니메이션의 참조·유지 호출 수를 읽어 60호출/초로 표시합니다. 시작/종료의 결합과 대기 복귀는 검토용이며 실제 게임의 입력·이벤트 분기를 실행하지 않습니다. 색/원점은 원래 팔레트와 160,160 기준이며 새 후보의 네이티브 패킹은 아직 전입니다.</small><select id="which"></select><select id="speed"><option value="1">1배(60호출/초)</option><option value="0.25" selected>0.25배(형태 검토)</option><option value="0.1">0.1배</option></select><button id="play">일시정지</button><button id="step">한 자세</button><span id="status"></span><h2>게임 원래 픽셀 크기</h2><canvas id="small0" width="96" height="72"></canvas><canvas id="small1" width="96" height="72"></canvas><h2>최근접 4배</h2><canvas id="big0" width="384" height="288"></canvas><canvas id="big1" width="384" height="288"></canvas><script>const data=DATA,cases=CASES;let frames={},run=true,index=0,elapsed=0,last=0;const names=Object.keys(cases);for(const x of names){let o=document.createElement('option');o.textContent=x;which.append(o)}let sequence=cases[names[0]];const ready=Promise.all(Object.entries(data).map(async([k,uris])=>{frames[k]=await Promise.all(uris.map(u=>new Promise(r=>{let im=new Image;im.onload=()=>r(im);im.src=u}))) }));function draw(){const q=sequence[index];document.getElementById('status').textContent='ref '+q.ref+' · '+q.calls+'호출';for(let side=0;side<2;side++){for(let prefix of ['small','big']){let c=document.getElementById(prefix+side),x=c.getContext('2d');x.imageSmoothingEnabled=false;x.clearRect(0,0,c.width,c.height);x.drawImage(frames[q.ref][side],0,0,c.width,c.height)}}}function advance(){index=(index+1)%sequence.length;draw()}which.onchange=()=>{sequence=cases[which.value];index=elapsed=0;draw()};play.onclick=()=>{run=!run;play.textContent=run?'일시정지':'재생'};step.onclick=()=>{run=false;play.textContent='재생';advance()};function tick(t){if(!last)last=t;const dt=Math.min(t-last,250);last=t;if(run){elapsed+=dt*Number(speed.value)*60/1000;while(elapsed>=sequence[index].calls){elapsed-=sequence[index].calls;advance()}}requestAnimationFrame(tick)}ready.then(()=>{draw();requestAnimationFrame(tick)})</script>'''
    html=html.replace('DATA',json.dumps(data,separators=(',',':'))).replace('CASES',json.dumps(cases,ensure_ascii=False,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8');write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'original_animation_manifest_sha256':p['prior_animation_manifest_sha256'],'frames':reports,'cases':cases,'clock_assumption':'60 calls per second; no game-event/control-flow emulation','runtime_verified':False,'native_packed':False,'html_sha256':digest(out/'REVIEW.html')});print(str(out/'REVIEW.html'))
if __name__=='__main__':main()
