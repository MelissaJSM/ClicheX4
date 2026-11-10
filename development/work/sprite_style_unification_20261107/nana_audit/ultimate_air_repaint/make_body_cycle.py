"""현재 11개 새 몸체를 실제 시간표와 같은 원점으로 비교한다."""
from pathlib import Path
import sys,json,io,base64
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from scripts.export_sprite_playback import read_disc,at,parse_sequence
def source(n):
 folder='hair53_registered_v2'if n==53 else'body_contacts_probe_v4'if n in(33,35,39,47)else'small_shoes_probe_v2'if n in(37,41)else'skin_edge_registered_v3'if n==51 else'before_second_registered_v1'if n==43 else'before_last_registered_v1'
 return D/folder/f'before_{n:03}.png'
def main():
 out=D/'body_cycle_v2';out.mkdir(exist_ok=False);a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());binpath=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';expected='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720';need(digest(binpath)==expected,'Parent BIN');exe=read_disc(binpath,['SLUS_005.61'])['SLUS_005.61']
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['ultimate_before']['animations']};cases={};tables=[]
 for aid,title in[(10,'상승 / 원표10'),(11,'하강 / 원표11'),(12,'착지 / 원표12')]:
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'Table pointer mismatch')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native step mismatch')
  seq=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];cases[title]=seq;tables.append(q)
 # A separate linking inspection does not claim to emulate event timing.
 cases['전후 연결 · 수동 비교 순서']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,*range(33,55,2),0)]
 data={};proof=[];idle=a.composite(0,15)[0];rows=[]
 for n in(0,*range(33,55,2)):
  new=idle if n==0 else a.rgba(np.array(Image.open(source(n))),16);ims=[idle,a.composite(n,15)[0],new];uris=[];hashes=[]
  for j,im in enumerate(ims):
   im=im.crop((112,120,208,192));im.save(out/f'{n:03}_{j}.png');b=io.BytesIO();im.save(b,format='PNG');uris.append('data:image/png;base64,'+base64.b64encode(b.getvalue()).decode());v=np.array(im);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=uris;proof.append({'ref':n,'hashes':hashes,'new_source':source(n).relative_to(ROOT).as_posix()if n else None,'new_file_sha256':digest(source(n))if n else None})
  if n:rows.append((f'ref{n}',[('accepted idle',idle),('old',a.composite(n,15)[0]),('new body candidate',new)]))
 for k,start in enumerate((0,4,8)):helper.grid(rows[start:start+4],out/f'sequence_{k+1}.png',4)
 html='''<!doctype html><meta charset="utf-8"><title>Nana Ultimate air bodies</title><style>body{font:15px sans-serif;background:#222831;color:#eee}canvas{background:#b6c0c7;image-rendering:pixelated;margin:5px}section{display:flex}button,select{font:inherit;margin:7px}small{display:block;max-width:1100px;line-height:1.6}</style><h2>나나 얼티밋 공중 11몸체 · 대기 / 기존 / 새 후보</h2><small>ARC 패킹 전 원화 등록 후보입니다. 실제 미국판 EXE 시간표 바이트를 검증했으며 60호출/초는 검토용 가정입니다. 입출력·물리·이벤트·총 발사는 실행하지 않습니다. 상대스텝0은 표 유지시간 후 검토용으로 처음부터 반복합니다. 수동 연결은 모든 자세에12호출을 주는 별도 비교이며 실제게임 타이밍이 아닙니다.</small><select id="which"></select><select id="speed"><option value="1">60호출/초 가정</option><option value="0.25">0.25배</option></select><button id="play">일시정지</button><button id="next">다음</button><span id="status"></span><section>SMALL</section><section>BIG</section><script>const DATA=DATAJSON,CASES=CASEJSON;let images={},seq=[],index=0,elapsed=0,last=0,running=true,draws=0,trace=[];const ready=Promise.all(Object.entries(DATA).map(async([k,v])=>images[k]=await Promise.all(v.map(u=>new Promise(resolve=>{let i=new Image;i.onload=()=>resolve(i);i.src=u})))));for(const k of Object.keys(CASES)){let o=document.createElement('option');o.value=o.textContent=k;which.append(o)}function draw(){let q=seq[index];status.textContent='ref '+q.ref;document.getElementById('status').textContent='ref '+q.ref+' / '+q.calls+'호출';for(let j=0;j<3;j++)for(let p of['small','big']){let c=document.getElementById(p+j),x=c.getContext('2d');x.imageSmoothingEnabled=false;x.clearRect(0,0,c.width,c.height);x.drawImage(images[q.ref][j],0,0,c.width,c.height)}draws++;trace.push(q.ref);if(trace.length>256)trace.shift()}function setCase(k){seq=CASES[k];index=elapsed=0;which.value=k;draw()}function step(){let s=seq[index].step;index=s?index+s:0;if(index<0||index>=seq.length)index=0;draw()}function pause(){running=false;play.textContent='재생'}function resume(){running=true;play.textContent='일시정지'}window.review={ready,setCase,selectRef(n){pause();seq=[{ref:n,calls:1,step:0}];index=0;draw()},pause,play:resume,step,cases:CASES,state:()=>({index,ref:seq[index].ref,draws,running,trace:trace.slice()})};which.onchange=()=>setCase(which.value);play.onclick=()=>running?pause():resume();next.onclick=()=>{pause();step()};function tick(t){if(!last)last=t;let dt=Math.min(t-last,250);last=t;if(running){elapsed+=dt*Number(speed.value)*60/1000;while(elapsed>=seq[index].calls){elapsed-=seq[index].calls;step()}}requestAnimationFrame(tick)}ready.then(()=>{setCase(Object.keys(CASES)[0]);requestAnimationFrame(tick)})</script>'''
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="72"></canvas>'for j in range(3))).replace('BIG',''.join(f'<canvas id="big{j}" width="384" height="288"></canvas>'for j in range(3))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,ensure_ascii=False,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 write(out/'manifest.json',{'parent_bin_sha256':expected,'exe_sha256':sha(exe),'arc_sha256':sha(a.data),'native_steps_exact':True,'tables':tables,'cases':cases,'frames':proof,'html_sha256':digest(out/'REVIEW.html'),'clock_assumption':'60 animate_object calls/second','native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
