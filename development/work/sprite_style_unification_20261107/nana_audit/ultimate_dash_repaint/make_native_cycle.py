"""대시20와 노바 머리3을 실제 EXE 순서로 보여주는 오프라인 검토판."""
from pathlib import Path
import sys,json,io,base64,ast
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
FINAL='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0'
def main():
 out=D/'native_cycle_v1';out.mkdir(exist_ok=False);old=Archive((D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC').read_bytes());new=Archive((D/'packed_dash_nova_diagnostic_v3/PL02_U.ARC').read_bytes());need(sha(new.data)==FINAL,'Candidate')
 source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(source)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','EXE source');exe=read_disc(source,['SLUS_005.61'])['SLUS_005.61'];meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['ultimate_before']['animations']};cases={};tables=[]
 for aid in(16,17,18,19,39,101,104,105,106,128,129):
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'Native table pointer')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native step')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 cases['수동 대시 몸체 / 임의12호출']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,*range(67,85,2),93,94,0)]
 cases['수동 대시 사격 / 임의12호출']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,*range(68,85,2),0)]
 refs=sorted({s['ref']for seq in cases.values()for s in seq});data={};frames=[];bounds=(96,96,320,240);w,h=bounds[2]-bounds[0],bounds[3]-bounds[1]
 for n in refs:
  # 엔진 표시 정책: 특수217..230은 획득 전후 모두 시각마스크15.
  aftermask=15 if 217<=n<=230 else 0
  images=[old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0],old.composite(0,0)[0],old.composite(n,aftermask)[0],new.composite(n,aftermask)[0]];urls=[];hashes=[]
  for j,im in enumerate(images):
   outside=np.asarray(im)[:,:,3].copy();outside[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not outside.any(),f'Crop clips {n}/{j}')
   crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());arr=np.asarray(crop).copy();arr[arr[:,:,3]==0]=0;hashes.append(sha(arr.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'after_visual_mask':aftermask,'canvas_rgba_sha256':hashes,'changed':n in {*range(67,85),93,94,217,218,220}})
 template=D.parent/'ultimate_wall_repaint/make_native_cycle.py';tree=ast.parse(template.read_text('utf8'));html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana Ultimate native dash review').replace('나나 얼티밋 벽 · ARC 재추출','나나 얼티밋 대시·노바 머리 · ARC 재추출').replace('실제 EXE 표 13·14·15·125·126·127','실제 EXE 표 16·17·18·19·39·101·104·105·106·128·129').replace('수동 전체 연결은 표와 별개입니다.','수동 전체 연결은 표와 별개입니다. 노바217~230은 두 의상 모두 엔진의 시각마스크15를 적용합니다. 93/94는 연결 자세이며 사격쌍이 아닙니다.').replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:1420px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="{w}" height="{h}"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="{w*2}" height="{h*2}"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,ensure_ascii=False,separators=(',',':')))
 (out/'REVIEW.html').write_text(html,'utf8');write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[w,h],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60 animation calls/sec; offline review only','renderer_policy':'Ultimate ownership before=mask15, after=mask0, special217..230=mask15 for both'});print(str(out))
if __name__=='__main__':main()
