"""미패킹 재킷16몸체의 원시간표/대기 연결 검토. 게임 실행 증거가 아니다."""
from pathlib import Path
import sys,json,io,base64,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from scripts.export_sprite_playback import read_disc,at
GROUPS={'first_contacts_probe_v1':(1,7,15,25),'second_contacts_probe_v2':(3,5,9,11),'third_contacts_probe_v2':(13,17,19,21),'fourth_contacts_probe_v1':(23,27,29,31)}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--hand31',action='store_true');args=parser.parse_args()
 out=D/('body_review_v2'if args.hand31 else'body_review_v1');out.mkdir(exist_ok=False);src=D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';need(digest(src)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Source');a=Archive(src.read_bytes());paths={n:D/g/f'before_{n:03}.png'for g,ns in GROUPS.items()for n in ns};need(set(paths)==set(range(1,33,2)),'All16')
 if args.hand31:paths[31]=D/'hand31_joint_probe_v1/before_031.png'
 source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(source)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','EXE parent');exe=read_disc(source,['SLUS_005.61'])['SLUS_005.61'];meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['ultimate_before']['animations']};cases={};tables=[]
 for aid in(8,38):
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'Pointer')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native step')
  cases[f'실제표 {aid}']=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step']}for s in q['steps']];tables.append(q)
 cases['수동 대기 연결 (임의12호출)']=[{'ref':n,'calls':12,'step':1}for n in(0,1,3,29,31,5,7,9,11,13,15,17,19,21,23,25,27,0)]
 data={};proof=[];window=(112,112,208,208)
 for n in(0,*range(1,33,2)):
  old=a.composite(n,15)[0];new=old if n==0 else a.rgba(np.array(Image.open(paths[n])),16);images=[a.composite(0,15)[0],old,new];urls=[];hashes=[]
  for j,im in enumerate(images):
   aa=np.array(im);alpha=aa[:,:,3].copy();alpha[112:208,112:208]=0;need(not alpha.any(),'Crop');crop=im.crop(window);crop.save(out/f'{n:03}_{j}.png');arr=np.array(crop);arr[arr[:,:,3]==0]=0;hashes.append(sha(arr.tobytes()));buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode())
  data[str(n)]=urls;proof.append({'ref':n,'source':str(paths[n].relative_to(ROOT))if n else'accepted idle from ARC','source_sha256':digest(paths[n])if n else sha(a.data),'canvas_rgba_sha256':hashes})
 html='''<!doctype html><meta charset="utf-8"><title>Nana run body candidate</title><style>body{background:#202630;color:#eee;font:15px sans-serif}canvas{image-rendering:pixelated;background:#bac4cb;margin:5px}section{display:flex}button,select{font:inherit;margin:6px}</style><h2>나나 얼티밋 이동 · 재킷16몸체 제작 중</h2><p>대기 / 기존 / 새 후보 순서.31 반대손 국소 보완 예정. 후폼·사격·ARC 패킹·실기는 아직 포함하지 않았습니다.</p><p>실제 EXE 유지시간·상대스텝,60호출/초 가정. 이벤트/물리/입력을 실행하지 않습니다. 수동 대기 연결은 별도 임의12호출입니다.</p><select id="which"></select><select id="speed"><option value="1">60호출/초</option><option value="0.25">0.25배</option></select><button id="play">일시정지</button><button id="next">다음</button><span id="status"></span><section>SMALL</section><section>BIG</section><script>const DATA=DATAJSON,CASES=CASEJSON;let images={},seq=[],index=0,elapsed=0,last=0,running=true,draws=0,trace=[];const ready=Promise.all(Object.entries(DATA).map(async([k,v])=>images[k]=await Promise.all(v.map(u=>new Promise(resolve=>{let i=new Image;i.onload=()=>resolve(i);i.src=u})))));for(const k of Object.keys(CASES)){let o=document.createElement('option');o.value=o.textContent=k;which.append(o)}function draw(){let q=seq[index];status.textContent='ref '+q.ref+' / '+q.calls;for(let j=0;j<3;j++)for(let p of['small','big']){let c=document.getElementById(p+j),x=c.getContext('2d');x.imageSmoothingEnabled=false;x.clearRect(0,0,c.width,c.height);x.drawImage(images[q.ref][j],0,0,c.width,c.height)}draws++;trace.push(q.ref);if(trace.length>256)trace.shift()}function setCase(k){seq=CASES[k];index=elapsed=0;which.value=k;draw()}function step(){let s=seq[index].step;index=s?index+s:0;if(index<0||index>=seq.length)index=0;draw()}function pause(){running=false;play.textContent='재생'}function resume(){running=true;play.textContent='일시정지'}window.review={ready,setCase,selectRef(n){pause();seq=[{ref:n,calls:1,step:0}];index=0;draw()},pause,play:resume,step,state:()=>({index,ref:seq[index].ref,draws,running,trace:trace.slice()})};which.onchange=()=>setCase(which.value);play.onclick=()=>running?pause():resume();next.onclick=()=>{pause();step()};function tick(t){if(!last)last=t;let dt=Math.min(t-last,250);last=t;if(running){elapsed+=dt*Number(speed.value)*60/1000;while(elapsed>=seq[index].calls){elapsed-=seq[index].calls;step()}}requestAnimationFrame(tick)}ready.then(()=>{setCase(Object.keys(CASES)[0]);requestAnimationFrame(tick)})</script>'''
 html=html.replace('status.textContent=',"document.getElementById('status').textContent=")
 if args.hand31:html=html.replace('31 반대손 국소 보완 예정.','31 새 반대손 국소 원화를 반영했습니다.')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="96"></canvas>'for j in range(3))).replace('BIG',''.join(f'<canvas id="big{j}" width="384" height="384"></canvas>'for j in range(3))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,ensure_ascii=False,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 write(out/'manifest.json',{'source_arc_sha256':digest(src),'exe_sha256':sha(exe),'tables':tables,'native_table_bytes_exact':True,'cases':cases,'frames':proof,'canvas_size':[96,96],'columns':3,'html_sha256':digest(out/'REVIEW.html'),'native_packed':False,'runtime_verified':False,'pending_local_art':[]if args.hand31 else[31],'clock_assumption':'60 animation calls/sec; no physics or event execution'})
 rows=[]
 for n in(0,1,3,29,31,5,7,9,11,13,15,17,19,21,23,25,27,0):
  v=a.composite(0,15)[0]if not n else a.rgba(np.array(Image.open(paths[n])),16);rows.append((f'{n:03}',v))
 for start in(0,9):
  sheet=Image.new('RGB',(9*192,240),(186,196,203));from PIL import ImageDraw
  dr=ImageDraw.Draw(sheet)
  for k,(label,im)in enumerate(rows[start:start+9]):sheet.paste(im.crop(window).resize((192,192),Image.Resampling.NEAREST),(k*192,35),im.crop(window).resize((192,192),Image.Resampling.NEAREST));dr.text((k*192+5,5),label,fill=(20,25,30))
  sheet.save(out/f'sequence_{start//9+1}.png')
 print(out)
if __name__=='__main__':main()
