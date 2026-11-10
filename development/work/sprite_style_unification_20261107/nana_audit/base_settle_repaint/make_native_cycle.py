"""실제 원표2/95/96에 포함되는 기본/포스138139를 재추출해 비교한다."""
from pathlib import Path
import sys,json,io,base64,ast,math
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
def main():
 out=D/'native_cycle_v1';out.mkdir(exist_ok=False);v=json.loads((D/'packed_settle_candidate_v1/verification.json').read_text('utf8'));old=Archive((ROOT/v['parent_path']).read_bytes());new=Archive((D/'packed_settle_candidate_v1/PL00_U.ARC').read_bytes());need(sha(new.data)==v['after'],'최종후보')
 plan=json.loads((D/'native_components_v1.json').read_text('utf8'));src=ROOT/plan['source_bin'];need(digest(src)==plan['source_sha256'],'EXE 원천');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61'];meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records=meta['characters']['nana']['forms']['base']['animations'];cases={};tables=[]
 for q in records:
  if not any(s['frame_ref']in(138,139)for s in q['steps']):continue
  aid=q['id'];need(at(exe,int(q['table_address'],16)+4*aid,4).hex()==q['pointer_bytes'],'원표포인터')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'원스텝')
  cases[str(aid)]=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];tables.append(q)
 need(set(cases)=={'2','95','96'},'138/139 전체 참조표')
 cases['manual idle-new89-new97-settle / 12 calls']=[{'ref':n,'calls':12,'step':1,'event':0}for n in(0,89,97,138,139,95,0)]
 refs=sorted({s['ref']for seq in cases.values()for s in seq});data={};frames=[];bounds=(96,96,224,224);w=h=128
 for n in refs:
  ims=[old.composite(0)[0],old.composite(n)[0],new.composite(n)[0],old.composite(0,15)[0],old.composite(n,15)[0],new.composite(n,15)[0]];urls=[];hashes=[]
  for j,im in enumerate(ims):
   alpha=np.array(im)[:,:,3];alpha[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not alpha.any(),f'창절단{n}/{j}');crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());z=np.array(crop);z[z[:,:,3]==0]=0;hashes.append(sha(z.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'canvas_rgba_sha256':hashes,'changed':n in(138,139)})
 tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'));html=next(q.value.value for q in ast.walk(tree)if isinstance(q,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in q.targets)and isinstance(q.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana base Fourth settle review').replace('나나 얼티밋 벽 · ARC 재추출','나나 기본/포스 138·139 · ARC 재추출').replace('전폼 대기 / 기존 / 새 후보 / 후폼 대기 / 기존 / 새 후보','기본 대기 / 기존 / 새 후보 / 포스 대기 / 기존 / 새 후보').replace('실제 EXE 표 13·14·15·125·126·127','실제 EXE 표2·95·96').replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:2400px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="{w}" height="{h}"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="{w*3}" height="{h*3}"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 for aid in(2,95,96):
  seq=cases[str(aid)];cols=min(6,len(seq));sheet=Image.new('RGB',(256*cols,538*math.ceil(len(seq)/cols)),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for i,s in enumerate(seq):
   x,y=i%cols*256,i//cols*538;dr.text((x+4,y+3),f'{s["ref"]} / {s["calls"]} calls / step{s["step"]}',fill='black')
   for j,mask in enumerate((0,15)):
    im=new.composite(s['ref'],mask)[0].crop(bounds).resize((256,256),Image.Resampling.NEAREST);sheet.paste(im,(x,y+26+j*256),im)
  sheet.save(out/f'timeline_{aid}.png')
 write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'source_bin':plan['source_bin'],'source_bin_sha256':plan['source_sha256'],'exe_sha256':sha(exe),'native_table_bytes_exact':True,'tables':tables,'cases':cases,'frames':frames,'window':bounds,'canvas_size':[w,h],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60호출/초 검토 가정. 원래 상대스텝/지속시간. 이벤트/물리/caller 미실행,step0은 검토 반복.','renderer_policy':'기본mask0 / 포스mask15 arm2.138139 이외는 최신부모 전체 불변.','scope':'등장 표2 전체를 보여주지만 새원화는138 한 자세×2의상,139 y−1 파생뿐이다. 다른 등장 원화와 실제 게임 완료로 세지 않는다.'});print(json.dumps({'refs':len(refs),'tables':len(tables),'canvas':6*len(refs),'candidate':sha(new.data)}))
if __name__=='__main__':main()
