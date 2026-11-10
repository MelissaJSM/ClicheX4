"""실제 새BIN/원표에서 재추출한 등장·사다리 연결을 오프라인 재생한다."""
from pathlib import Path
import sys,json,base64,io,math
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc,require
from scripts.export_x_consistency import Archive
from scripts.export_sprite_playback import at
from src.psx_disc import file_hash
OUT=ROOT/'out/sprite_style_unification_20261107/resumed51'
def main():
 require(not OUT.exists(),'Fresh review');OUT.mkdir();meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));cases=[];sources={};tables=[]
 for char,mode,version,stem,ids in [('shibuki','ver_buki_riko',32,'shibuki_riko',[2]),('nana','ver_rin_nana',44,'rin_nana',[27,28,29,30,31,32,92,93])]:
  folder=ROOT/f'out/{mode}/sprite_style_unification_20261107_v{version}';bn=folder/f'{stem}.bin';manifest=json.loads((folder/'manifest.json').read_text('utf8'));require(file_hash(bn)==manifest['modified_bin']['sha256'],'BIN hash');assets,_=read_disc(bn,('PL02_U.ARC','SLUS_005.61'));a=Archive(assets['PL02_U.ARC']);exe=assets['SLUS_005.61'];sources[char]={'bin':bn.relative_to(ROOT).as_posix(),'sha256':file_hash(bn)}
  for q in meta['characters'][char]['forms']['ultimate_after']['animations']:
   if q['id']not in ids:continue
   require(at(exe,int(q['table_address'],16)+4*q['id'],4).hex()==q['pointer_bytes'],'Table pointer');steps=[]
   for s in q['steps']:
    require(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Table step');n=s['frame_ref'];pair=Image.new('RGBA',(256,128));hashes=[]
    for i,mask in enumerate((15,0)):
     full=a.composite(n,mask)[0];alpha=np.array(full)[:,:,3];alpha[96:224,96:224]=0;require(not alpha.any(),'Crop cut');crop=full.crop((96,96,224,224));pair.alpha_composite(crop,(i*128,0));hashes.append(__import__('hashlib').sha256(crop.tobytes()).hexdigest())
    buf=io.BytesIO();pair.save(buf,format='PNG');steps.append({'ref':n,'calls':s['duration_calls'],'relative':s['relative_step'],'event':s['event'],'source_rgba':hashes,'image':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()})
   cid=f'{char}_{q["id"]}';cases.append({'id':cid,'steps':steps});tables.append({'id':cid,'table_address':q['table_address'],'pointer_bytes':q['pointer_bytes'],'native_steps':[s['bytes']for s in q['steps']]})
   if q['id']in (2,28,31,92):
    selected=steps if q['id']!=2 else steps[7:14];cols=min(8,len(selected));sheet=Image.new('RGB',(160*cols,338*math.ceil(len(selected)/cols)),'#1e2530');dr=ImageDraw.Draw(sheet)
    for j,s in enumerate(selected):
     x,y=j%cols*160,j//cols*338;dr.text((x+4,y+4),f'{s["ref"]}: {s["calls"]} calls',fill='white')
     for k,mask in enumerate((15,0)):
      pic=a.composite(s['ref'],mask)[0].crop((120,116,200,196)).resize((160,160),Image.Resampling.NEAREST);sheet.paste(pic,(x,y+18+k*160),pic)
    sheet.save(OUT/f'{cid}_timeline.png')
 html='''<!doctype html><meta charset="utf-8"><title>보정 재개 51 · 원표 재생</title><style>body{background:#151c25;color:#e9eef3;font:16px system-ui;margin:24px}canvas{background:#252f3d;image-rendering:pixelated;border:1px solid #48576b}section{margin:20px 0}button,select{font:inherit;margin:6px;padding:6px}p{max-width:1000px;line-height:1.5}</style><h1>시부키 등장 · 나나 사다리 보정</h1><p>새 BIN에서 재추출했습니다. 왼쪽은 재킷, 오른쪽은 캡슐 획득 후 의상입니다. 원게임의 순서·상대 이동·유지 호출수를 사용합니다. 60호출/초는 미리보기 가정이며 실제 이동·사다리 접점·효과 객체·이벤트·호출자 상태는 실행하지 않습니다. 92/93의 긴 유지시간은 호출자가 바꾸기도 합니다.</p><select id="case"></select><button id="play">재생 / 정지</button><button id="next">다음 프레임</button><button id="reset">처음</button><select id="speed"><option value="1">원속도 가정</option><option value="0.25">1/4 속도</option></select><p id="info"></p><canvas id="c" width="512" height="256"></canvas><script>const DATA=DATAJSON;let ci=0,si=0,run=false,acc=0,last=0;const imgs=DATA.map(c=>c.steps.map(s=>{const i=new Image;i.src=s.image;return i}));const el=document.querySelector('#case'),canvas=document.querySelector('#c'),ctx=canvas.getContext('2d');ctx.imageSmoothingEnabled=false;el.innerHTML=DATA.map((c,i)=>`<option value="${i}">${c.id}</option>`).join('');function draw(){let s=DATA[ci].steps[si];ctx.clearRect(0,0,512,256);ctx.drawImage(imgs[ci][si],0,0,512,256);document.querySelector('#info').textContent=`${DATA[ci].id} · ${si+1}/${DATA[ci].steps.length} · 참조 ${s.ref} · ${s.calls} 호출`;window.shown={case:ci,step:si,ref:s.ref};}window.showFrame=(c,s)=>{run=false;ci=c;si=s;el.value=c;acc=0;draw()};el.onchange=()=>showFrame(+el.value,0);document.querySelector('#play').onclick=()=>{run=!run;acc=0};document.querySelector('#next').onclick=()=>showFrame(ci,(si+1)%DATA[ci].steps.length);document.querySelector('#reset').onclick=()=>showFrame(ci,0);function tick(t){if(last&&run){acc+=(t-last)*60/1000*(+document.querySelector('#speed').value);let s=DATA[ci].steps[si];while(acc>=s.calls){acc-=s.calls;let ni=si+s.relative;if(!s.relative||ni<0||ni>=DATA[ci].steps.length){run=false;break}si=ni;s=DATA[ci].steps[si];draw()}}last=t;requestAnimationFrame(tick)}Promise.all(imgs.flat().map(i=>i.decode())).then(()=>{draw();window.ready=true;requestAnimationFrame(tick)});</script>'''.replace('DATAJSON',json.dumps(cases,separators=(',',':')))
 (OUT/'REVIEW.html').write_text(html,'utf8');report={'sources':sources,'native_table_bytes_exact':True,'tables':tables,'cases':[{'id':c['id'],'steps':[{k:v for k,v in s.items()if k!='image'}for s in c['steps']]}for c in cases],'html_sha256':file_hash(OUT/'REVIEW.html'),'gameplay_verified':False,'offline_simulation':True};(OUT/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'cases':len(cases),'steps':sum(len(c['steps'])for c in cases)}))
if __name__=='__main__':main()
