"""실제 탑승 원표65~76을 읽고 고정 원점·호출수의 오프라인 검토판을 만든다."""
from pathlib import Path
import sys,json,io,base64,ast,math
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
from pack_native import PARENT,REFS
def main():
 out=D/'native_cycle_v1';out.mkdir(exist_ok=False);old=Archive(PARENT.read_bytes());cp=D/'packed_vehicle_candidate_v1/PL02_U.ARC';new=Archive(cp.read_bytes());src=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v34/rin_nana.bin';need(digest(src)=='43b63a99328f4aa4e2aa004e8799834397efe91ff4510a36d4cd6b4dd48445d0','RN34');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61']
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['base']['animations']};cases={};tables=[]
 for aid in range(65,77):
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'원표포인터')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'원스텝')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 refs=sorted({s['ref']for seq in cases.values()for s in seq});need(refs==list(REFS),'실제13참조');data={};frames=[];bounds=(112,112,208,208);w=h=96
 for n in refs:
  ims=[old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0],old.composite(0)[0],old.composite(n)[0],new.composite(n)[0]];urls=[];hashes=[]
  for j,im in enumerate(ims):
   alpha=np.array(im)[:,:,3];alpha[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not alpha.any(),f'창절단{n}/{j}');crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes,'changed':True})
 tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'));html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana Ultimate vehicle native review').replace('나나 얼티밋 벽 · ARC 재추출','나나 얼티밋 탑승13 · ARC 재추출').replace('실제 EXE 표 13·14·15·125·126·127','실제 EXE 표65~76. 새4자세와 원Y별칭9개의 양폼. 실제 차량 물리/배경/손잡이 실행은 별도').replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:1950px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="96"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="288" height="288"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 for aid in range(65,77):
  seq=cases[str(aid)];cols=min(6,len(seq));sheet=Image.new('RGB',(192*cols,414*math.ceil(len(seq)/cols)),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for i,s in enumerate(seq):
   x,y=i%cols*192,i//cols*414;dr.text((x+4,y+3),f'{s["ref"]} / {s["calls"]} calls / step{s["step"]}',fill='black');dr.text((x+4,y+15),'NEW SHARED Y ALIAS'if s['ref']not in(162,166,170,174)else'NEW SOURCE BODY',fill='#006050')
   for j,mask in enumerate((15,0)):
    im=new.composite(s['ref'],mask)[0].crop(bounds).resize((192,192),Image.Resampling.NEAREST);sheet.paste(im,(x,y+29+j*192),im)
  sheet.save(out/f'timeline_{aid}.png')
 write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[w,h],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60호출/초 검토가정. 상대스텝/지속시간은 원값이며 이벤트/차량물리/caller 미실행. 상대0은 검토반복처리.','changed_refs':list(REFS),'scope':'원표65~76의13참조/양폼을 연결한 정적·기계재생검토. 원Y별칭9개의 맨팔 적용은 새공통정책. 실제게임·인간실시간관찰·차량 배경과의 접점은 별도.'});print(json.dumps({'refs':len(refs),'tables':12,'canvas':len(refs)*6,'sha256':sha(new.data)}))
if __name__=='__main__':main()
