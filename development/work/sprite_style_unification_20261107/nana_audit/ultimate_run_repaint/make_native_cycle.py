"""새 이동32 실제 ARC와 원 EXE 표7종을 재생하는 오프라인 검토판."""
from pathlib import Path
import sys,json,io,base64,ast
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
FINAL='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
def main():
 out=D/'native_cycle_v1';out.mkdir(exist_ok=False)
 old=Archive((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());new=Archive((D/'packed_run_diagnostic_v1/PL02_U.ARC').read_bytes());need(sha(new.data)==FINAL,'Candidate')
 src=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(src)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','EXE source BIN')
 exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61'];meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'))
 records={q['id']:q for q in meta['characters']['nana']['forms']['ultimate_before']['animations']};cases={};tables=[]
 for aid in(7,8,38,119,120,16,128):
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'Native table pointer')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native step')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 order=(0,1,3,29,31,5,7,9,11,13,15,17,19,21,23,25,27,0)
 cases['수동 대기/몸체 연결 · 임의12호출']=[{'ref':n,'calls':12,'step':1,'event':0}for n in order]
 cases['수동 대기/사격 연결 · 임의12호출']=[{'ref':n+1 if n else 0,'calls':12,'step':1,'event':0}for n in order]
 refs=sorted({s['ref']for seq in cases.values()for s in seq});data={};frames=[];bounds=(80,104,240,200);w,h=bounds[2]-bounds[0],bounds[3]-bounds[1]
 for n in refs:
  images=[old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0],old.composite(0,0)[0],old.composite(n,0)[0],new.composite(n,0)[0]];urls=[];hashes=[]
  for j,im in enumerate(images):
   outside=np.array(im)[:,:,3];outside[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not outside.any(),f'Crop loss {n}/{j}')
   crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode())
   v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes,'changed':1<=n<=32})
 tree=ast.parse((D.parent/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'))
 html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana Ultimate native run review').replace('나나 얼티밋 벽 · ARC 재추출','나나 얼티밋 이동32 · ARC 재추출').replace('실제 EXE 표 13·14·15·125·126·127','실제 EXE 표 7·8·38·119·120·16·128')
 html=html.replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:1950px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="{w}" height="{h}"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="{w*2}" height="{h*2}"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,ensure_ascii=False,separators=(',',':')))
 (out/'REVIEW.html').write_text(html,'utf8')
 for aid in(7,8,38,119,120,16,128):
  seq=cases[str(aid)];sheet=Image.new('RGB',(192*len(seq),360),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for i,s in enumerate(seq):
   dr.text((192*i+4,3),f'{s["ref"]} / {s["calls"]} calls',fill='black')
   for j,mask in enumerate((15,0)):
    im=new.composite(s['ref'],mask)[0].crop((112,112,208,192)).resize((192,160),Image.Resampling.NEAREST);sheet.paste(im,(192*i,30+160*j),im)
  sheet.save(out/f'timeline_{aid}.png')
 write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'native_table_bytes_exact':True,
  'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[w,h],'html_sha256':digest(out/'REVIEW.html'),
  'runtime_verified':False,'clock_assumption':'60 animation calls/sec; offline only; terminal relative-step0 is preview replay',
  'renderer_policy':'Ultimate before=mask15, after=mask0. Original dash refs67..76 unchanged in transitions16/128.'})
 print(json.dumps({'output':str(out),'refs':len(refs),'native_tables':len(tables)}))
if __name__=='__main__':main()
