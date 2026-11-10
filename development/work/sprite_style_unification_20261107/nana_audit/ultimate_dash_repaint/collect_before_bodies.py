"""대시 전폼10 새 몸체를 출처와 함께 모아 원시간표 미패킹 검토판 생성."""
from pathlib import Path
import sys,json,io,base64
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED
from scripts.export_sprite_playback import read_disc,at
SOURCES={67:'first_cases_probe_v2',69:'more_cases_probe_v2',71:'local_legs_registered_v4',75:'more_cases_probe_v2',77:'more_cases_probe_v2',79:'first_cases_probe_v2',81:'more_cases_probe_v2',83:'more_cases_probe_v2',93:'first_cases_probe_v2',94:'fold94_registered_v1'}
def main():
 need(digest(SRC)==EXPECTED,'Frozen parent');out=D/'before_bodies_review_v1';out.mkdir(exist_ok=False);a=Archive(SRC.read_bytes());new={};records=[];rows=[]
 for n,folder in SOURCES.items():
  p=D/folder/f'before_{n:03}.png';ar=np.array(Image.open(p));need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Native index');new[n]=a.rgba(ar,16);Image.fromarray(ar).save(out/f'before_{n:03}.png');new[n].save(out/f'before_{n:03}_rgba.png');y,x=np.nonzero(ar)
  records.append({'ref':n,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'indexed_sha256':sha(ar.tobytes()),'bbox_world':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'sole_y':int(y.max()-160),'generated_local_or_whole_art':True})
  rows.append((str(n),[('accepted idle',a.composite(0,15)[0]),('old game',a.composite(n,15)[0]),('new body / not packed',new[n])]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',5)
 source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(source)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','EXE source');exe=read_disc(source,['SLUS_005.61'])['SLUS_005.61'];meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));anims={q['id']:q for q in meta['characters']['nana']['forms']['ultimate_before']['animations']};cases={};tables=[]
 for aid in(16,17,18,19):
  q=anims[aid];need(at(exe,int(q['table_address'],16)+aid*4,4).hex()==q['pointer_bytes'],'Native pointer')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native steps')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 cases['manual 10 bodies']=[{'ref':r,'calls':12,'step':1,'event':0}for r in(0,*SOURCES,0)]
 refs=sorted({s['ref']for seq in cases.values()for s in seq});data={};frames=[];bounds=(112,112,208,192)
 for n in refs:
  # 73 효과는 아직 미통합이다. 검토판에서71의 새 몸체만 임시로 표시함을 명시한다.
  revised=new.get(n,new[71]if n==73 else a.composite(n,15)[0]);images=[a.composite(0,15)[0],a.composite(n,15)[0],revised];urls=[];hashes=[]
  for j,im in enumerate(images):
   ar=np.array(im);outside=ar[:,:,3].copy();outside[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not outside.any(),'Canvas crop clips')
   crop=im.crop(bounds);crop.save(out/f'canvas_{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());ar=np.array(crop);ar[ar[:,:,3]==0]=0;hashes.append(sha(ar.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes,'status':'body71 proxy, effects absent'if n==73 else'new body candidate'if n in new else'unchanged source reference'})
 html='''<!doctype html><meta charset="utf-8"><title>Nana Ultimate dash bodies</title><style>body{font:15px sans-serif;background:#222831;color:#eee}canvas{background:#b6c0c7;image-rendering:pixelated;margin:5px}section{display:flex}select,button{font:inherit;margin:8px}small{display:block;line-height:1.6}</style><h2>나나 얼티밋 대시 · 전폼 몸체 중간 검토</h2><small>대기 / 기존 / 새 원화 등록. 새 ARC 재추출·실기 아님. 16~19 원시간표, 60호출/초 가정.73은71 새몸체 대체표시이며 원스파크 미합성,1·3은 기존 이동. 사격·후폼·이벤트 실행은 제외.</small><select id="which"></select><select id="speed"><option value="1">60 calls/s</option><option value="0.25">0.25x</option></select><button id="play">일시정지</button><button id="next">다음</button><span id="status"></span><section>SMALL</section><section>BIG</section><script>const DATA=DATAJSON,CASES=CASEJSON;let images={},seq=[],index=0,elapsed=0,last=0,running=true,draws=0,trace=[];const ready=Promise.all(Object.entries(DATA).map(async([k,v])=>images[k]=await Promise.all(v.map(u=>new Promise(resolve=>{let i=new Image;i.onload=()=>resolve(i);i.src=u})))));for(const k of Object.keys(CASES)){let o=document.createElement('option');o.value=o.textContent=k;which.append(o)}function draw(){let q=seq[index];document.getElementById('status').textContent='ref '+q.ref+' / '+q.calls+' calls'+(q.ref===73?' / body71 proxy, no effects':'');for(let j=0;j<3;j++)for(let p of['small','big']){let c=document.getElementById(p+j),x=c.getContext('2d');x.imageSmoothingEnabled=false;x.clearRect(0,0,c.width,c.height);x.drawImage(images[q.ref][j],0,0,c.width,c.height)}draws++;trace.push(q.ref);if(trace.length>256)trace.shift()}function setCase(k){seq=CASES[k];index=elapsed=0;which.value=k;draw()}function step(){let s=seq[index].step;index=s?index+s:0;if(index<0||index>=seq.length)index=0;draw()}function pause(){running=false;play.textContent='재생'}function resume(){running=true;play.textContent='일시정지'}window.review={ready,setCase,selectRef(n){pause();seq=[{ref:n,calls:1,step:0}];index=0;draw()},pause,play:resume,step,cases:CASES,state:()=>({index,ref:seq[index].ref,draws,running,trace:trace.slice()})};which.onchange=()=>setCase(which.value);play.onclick=()=>running?pause():resume();next.onclick=()=>{pause();step()};function tick(t){if(!last)last=t;let dt=Math.min(t-last,250);last=t;if(running){elapsed+=dt*Number(speed.value)*60/1000;while(elapsed>=seq[index].calls){elapsed-=seq[index].calls;step()}}requestAnimationFrame(tick)}ready.then(()=>{setCase(Object.keys(CASES)[0]);requestAnimationFrame(tick)})</script>'''
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="80"></canvas>'for j in range(3))).replace('BIG',''.join(f'<canvas id="big{j}" width="384" height="320"></canvas>'for j in range(3))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'records':records,'frames':frames,'tables':tables,'cases':cases,'native_table_bytes_exact':True,'exe_sha256':sha(exe),'html_sha256':digest(out/'REVIEW.html'),'crop':bounds,'native_packed':False,'runtime_verified':False,'limits':['73 is body71 proxy without effects','1/3 unchanged old run','after costume and shooting pending','60 calls/sec review assumption, events not executed']});print(out)
if __name__=='__main__':main()
