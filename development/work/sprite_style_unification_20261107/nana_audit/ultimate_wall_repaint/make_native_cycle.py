"""완성 후보 ARC와 원본 EXE 시간표로 벽 전후 의상 검토기를 만든다."""
from pathlib import Path
import sys,json,io,base64
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at

def main():
 out=D/'native_cycle_v2';out.mkdir(exist_ok=False)
 old=Archive((D.parent/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());new=Archive((D/'packed_wall_candidate_v1/PL02_U.ARC').read_bytes())
 need(sha(new.data)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Candidate')
 source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(source)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','EXE source BIN')
 exe=read_disc(source,['SLUS_005.61'])['SLUS_005.61'];meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'))
 records={q['id']:q for q in meta['characters']['nana']['forms']['ultimate_before']['animations']};cases={};tables=[]
 for aid,name in[(13,'벽 13'),(14,'벽 14 / 벽39 복귀'),(15,'벽 15'),(125,'벽 사격125'),(126,'벽 사격126 / 벽40 복귀'),(127,'벽 사격127')]:
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'Native table pointer')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native step')
  seq=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']]
  need(all(s['ref']in {39,40,*range(55,67)}for s in seq),'Out-of-group step');cases[f'{aid}: {name}']=seq;tables.append(q)
 cases['전체 몸체 연결 / 임의12호출']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,*range(55,67,2),0)]
 cases['전체 사격 연결 / 임의12호출']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,*range(56,67,2),0)]
 data={};frames=[];bounds=(112,112,208,192)
 for n in(0,39,40,*range(55,67)):
  images=[old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0],old.composite(0,0)[0],old.composite(n,0)[0],new.composite(n,0)[0]];urls=[];hashes=[]
  for j,im in enumerate(images):
   outside=np.asarray(im)[:,:,3].copy();outside[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not outside.any(),'Review crop clips image')
   crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode())
   arr=np.asarray(crop).copy();arr[arr[:,:,3]==0]=0;hashes.append(sha(arr.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes})
 html='''<!doctype html><meta charset="utf-8"><title>Nana Ultimate native wall review</title><style>body{font:15px sans-serif;background:#222831;color:#eee}canvas{background:#b6c0c7;image-rendering:pixelated;margin:4px}section{display:flex;gap:4px}button,select{font:inherit;margin:6px}small{display:block;max-width:1400px;line-height:1.6}</style><h2>나나 얼티밋 벽 · ARC 재추출</h2><small>각 줄: 전폼 대기 / 기존 / 새 후보 / 후폼 대기 / 기존 / 새 후보. 실제 EXE 표 13·14·15·125·126·127의 유지시간과 상대스텝입니다. 60호출/초는 검토용 가정이며 물리·입력·이벤트 복귀·발사를 실행하지 않습니다. 상대스텝0은 유지시간 뒤 검토용 반복으로 처리합니다. 수동 전체 연결은 표와 별개입니다.</small><select id="which"></select><select id="speed"><option value="1">60호출/초 가정</option><option value="0.25">0.25배</option></select><button id="play">일시정지</button><button id="next">다음</button><span id="status"></span><section>SMALL</section><section>BIG</section><script>const DATA=DATAJSON,CASES=CASEJSON;let images={},seq=[],index=0,elapsed=0,last=0,running=true,draws=0,trace=[];const ready=Promise.all(Object.entries(DATA).map(async([k,v])=>images[k]=await Promise.all(v.map(u=>new Promise(resolve=>{let i=new Image;i.onload=()=>resolve(i);i.src=u})))));for(const k of Object.keys(CASES)){let o=document.createElement('option');o.value=o.textContent=k;which.append(o)}function draw(){let q=seq[index];document.getElementById('status').textContent='ref '+q.ref+' / '+q.calls+'호출';for(let j=0;j<6;j++)for(let p of['small','big']){let c=document.getElementById(p+j),x=c.getContext('2d');x.imageSmoothingEnabled=false;x.clearRect(0,0,c.width,c.height);x.drawImage(images[q.ref][j],0,0,c.width,c.height)}draws++;trace.push(q.ref);if(trace.length>256)trace.shift()}function setCase(k){seq=CASES[k];index=elapsed=0;which.value=k;draw()}function step(){let s=seq[index].step;index=s?index+s:0;if(index<0||index>=seq.length)index=0;draw()}function pause(){running=false;play.textContent='재생'}function resume(){running=true;play.textContent='일시정지'}window.review={ready,setCase,selectRef(n){pause();seq=[{ref:n,calls:1,step:0}];index=0;draw()},pause,play:resume,step,cases:CASES,state:()=>({index,ref:seq[index].ref,draws,running,trace:trace.slice()})};which.onchange=()=>setCase(which.value);play.onclick=()=>running?pause():resume();next.onclick=()=>{pause();step()};function tick(t){if(!last)last=t;let dt=Math.min(t-last,250);last=t;if(running){elapsed+=dt*Number(speed.value)*60/1000;while(elapsed>=seq[index].calls){elapsed-=seq[index].calls;step()}}requestAnimationFrame(tick)}ready.then(()=>{setCase(Object.keys(CASES)[0]);requestAnimationFrame(tick)})</script>'''
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="80"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="288" height="240"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,ensure_ascii=False,separators=(',',':')))
 (out/'REVIEW.html').write_text(html,'utf8');write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60 animation calls/sec; offline review only'});print(str(out))
if __name__=='__main__':main()
