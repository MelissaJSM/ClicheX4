"""실제 EXE 호버12표의 원시간/스텝을 최종 ARC로 정적·오프라인 검토한다."""
from pathlib import Path
import sys,json,io,base64,ast,math,re
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;W=D.parent;N=W/'nana_audit';ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
PARENT=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';REFS=tuple(range(221,231))
def main():
 out=D/'native_cycle01';out.mkdir(exist_ok=False);old=Archive(PARENT.read_bytes());cp=D/'packed_hover_final01/PL00_U.ARC';new=Archive(cp.read_bytes());plan=json.loads((D/'native_components01.json').read_text('utf8'));src=ROOT/plan['source_bin'];need(digest(src)==plan['source_sha256'],'RN36');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61']
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['fourth']['animations']};cases={};tables=[];ids=[*range(21,27),*range(133,139)]
 for aid in ids:
  q=records[aid];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'원표포인터')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'원스텝')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 refs=sorted({s['ref']for seq in cases.values()for s in seq});need(set(refs)=={45,46,47,48,*REFS},'실제14참조');data={};frames=[];bounds=(112,112,208,208)
 for n in refs:
  mask=8 if n>=217 else 0
  ims=[old.composite(n,mask)[0],new.composite(n,mask)[0],old.composite(n,15)[0],new.composite(n,15)[0],new.rgba(new.layer(n,0)[0]),new.rgba(new.layer(n,8)[0],16)];urls=[];hashes=[]
  for j,im in enumerate(ims):
   alpha=np.array(im)[:,:,3];alpha[112:208,112:208]=0;need(not alpha.any(),f'창절단{n}/{j}');crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'actual_comparison_mask':mask,'canvas_rgba_sha256':hashes,'changed':n in REFS})
 tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'));html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana basic Fourth hover native review');html=re.sub(r'<h2>.*?</small>','<h2>나나 기본/포스 호버10 · ARC 재추출</h2><small>각 줄: 기존 기본+다리 / 새 기본+다리 / 기존 포스 / 새 포스 / 새0층 / 새8층. 호버는 다리 bit8을 사용하며 Ultimate의 강제mask15 규칙을 적용하지 않는다. 연결공중은 기본0/포스15다. 마지막 두 층은 불완전한 진단표시다. 실제 EXE 표21~26/133~138 유지시간·상대스텝. 60호출/초는 검토 가정이며 입력·물리·이벤트·별도 추진불꽃과 탄환 객체를 실행하지 않는다. 상대스텝0은 검토용 반복이다.</small>',html,flags=re.S)
 html=html.replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:1950px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="96"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="288" height="288"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 for aid in ids:
  seq=cases[str(aid)];cols=min(6,len(seq));sheet=Image.new('RGB',(192*cols,414*math.ceil(len(seq)/cols)),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for i,s in enumerate(seq):
   n=s['ref'];mask=8 if n>=217 else 0;x,y=i%cols*192,i//cols*414;dr.text((x+4,y+3),f'{n} / {s["calls"]} calls / step{s["step"]}',fill='black');dr.text((x+4,y+15),f'OLD / NEW actual mask{mask}',fill='#006050')
   for j,a in enumerate((old,new)):
    im=a.composite(n,mask)[0].crop(bounds).resize((192,192),Image.Resampling.NEAREST);sheet.paste(im,(x,y+29+j*192),im)
  sheet.save(out/f'timeline_{aid}.png')
 write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'source_bin':plan['source_bin'],'source_bin_sha256':plan['source_sha256'],'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[96,96],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60호출/초 검토 가정. 원표 상대스텝/지속시간 보존, 이벤트/caller 물리 미실행. 상대0 검토반복.','changed_refs':list(REFS),'scope':'실제12표·14참조84canvas의 정적·기계재생. 별도 추진불꽃/탄환은 정적 원점판으로 분리하며 게임 실기/인간 실시간 관찰과 다르다.'});print(json.dumps({'refs':len(refs),'tables':len(ids),'canvas':len(refs)*6,'sha256':sha(new.data)}))
if __name__=='__main__':main()
