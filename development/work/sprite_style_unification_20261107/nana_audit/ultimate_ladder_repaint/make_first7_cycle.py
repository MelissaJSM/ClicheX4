"""허용7 사다리와 그대로남은7의 실제표27..32를 분리표시한다."""
from pathlib import Path
import sys,json,io,base64,ast,math
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
from pack_first7 import PARENT,REFS
def main():
 out=D/'first7_native_cycle_v1';out.mkdir(exist_ok=False);old=Archive(PARENT.read_bytes());cp=D/'packed_first7_diagnostic_v1/PL02_U.ARC';new=Archive(cp.read_bytes());src=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v27/rin_nana.bin';need(digest(src)=='62e3850cf773bb013eebda6c22eee23ba37ca69ff5ac06baa5f601e712f2b7a1','RN27');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61']
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['base']['animations']};cases={};tables=[]
 for aid in range(27,33):
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'원표포인터')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'원스텝')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 refs=sorted({s['ref']for seq in cases.values()for s in seq});data={};frames=[];bounds=(112,112,208,208);w=h=96
 for n in refs:
  ims=[old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0],old.composite(0)[0],old.composite(n)[0],new.composite(n)[0]];urls=[];hashes=[]
  for j,im in enumerate(ims):
   alpha=np.array(im)[:,:,3];alpha[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not alpha.any(),f'창절단{n}/{j}');crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes,'changed':n in REFS})
 tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'));html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana ladder first7 native review').replace('나나 얼티밋 벽 · ARC 재추출','나나 사다리 허용7 · ARC 재추출').replace('실제 EXE 표 13·14·15·125·126·127','실제 EXE 표27..32. 새참조143/144/145/146/147/154/183만 변경. 보류148/149/150/151/152/153/155와이동1은이전그림').replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:1950px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="96"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="288" height="288"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 for aid in range(27,33):
  seq=cases[str(aid)];cols=min(6,len(seq));sheet=Image.new('RGB',(192*cols,414*math.ceil(len(seq)/cols)),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for i,s in enumerate(seq):
   x,y=i%cols*192,i//cols*414;dr.text((x+4,y+3),f'{s["ref"]} / {s["calls"]} calls / step{s["step"]}',fill='black');dr.text((x+4,y+15),'NEW'if s['ref']in REFS else'PRESERVED',fill='#006050'if s['ref']in REFS else'#8c3232')
   for j,mask in enumerate((15,0)):
    im=new.composite(s['ref'],mask)[0].crop(bounds).resize((192,192),Image.Resampling.NEAREST);sheet.paste(im,(x,y+29+j*192),im)
  sheet.save(out/f'timeline_{aid}.png')
 write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[w,h],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60호출/초 검토가정.상대스텝/지속시간은원값이며이벤트/물리/caller미실행.상대0은검토반복처리.','changed_refs':list(REFS),'remaining_ladder_refs':[148,149,150,151,152,153,155],'scope':'허용7 신규후보와나머지보존그림이섞인 원표27..32의정적/기계재생검토. 전체사다리 완료나새사격150155검증이아님.'});print(json.dumps({'refs':len(refs),'tables':6,'canvas':len(refs)*6,'sha256':sha(new.data)}))
if __name__=='__main__':main()
