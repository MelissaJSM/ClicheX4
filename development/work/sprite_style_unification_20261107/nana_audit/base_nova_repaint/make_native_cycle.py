"""PL00 노바 원표106의 준비→돌진/효과 순서와 실제기본/포스 표시를 읽는다."""
from pathlib import Path
import sys,json,io,base64,ast,re
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
from pack_candidate import PARENT
REFS=tuple(range(213,221))
def main():
 out=D/'native_cycle_v1';out.mkdir(exist_ok=False);old=Archive(PARENT.read_bytes());new=Archive((D/'packed_nova_candidate_v1/PL00_U.ARC').read_bytes());plan=json.loads((D/'native_components_v1.json').read_text('utf8'));src=ROOT/plan['source_bin'];need(digest(src)==plan['source_sha256'],'RN41');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61']
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));records={q['id']:q for q in meta['characters']['nana']['forms']['base']['animations']};q=records[106];need(at(exe,int(q['table_address'],16)+4*106,4).hex()==q['pointer_bytes'],'원표106 포인터')
 for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'원스텝106')
 seq=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event']}for s in q['steps']];need(set(s['ref']for s in seq)==set(REFS)and len(seq)==13,'원표13스텝8참조');cases={'106':seq};bounds=(96,112,256,208);width,height=160,96;data={};frames=[]
 for n in REFS:
  postmask=15;ims=[old.composite(n,0)[0],new.composite(n,0)[0],old.composite(n,postmask)[0],new.composite(n,postmask)[0],old.rgba(old.layer(n,5)[0],16),new.rgba(new.layer(n,5)[0],16)];urls=[];hashes=[]
  for j,im in enumerate(ims):
   alpha=np.array(im)[:,:,3];alpha[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not alpha.any(),f'에너지끝 창절단{n}/{j}');crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'before_mask':0,'after_actual_mask':postmask,'canvas_rgba_sha256':hashes})
 tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'));html=next(z.value.value for z in ast.walk(tree)if isinstance(z,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in z.targets)and isinstance(z.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana base Fourth Nova native review');html=re.sub(r'<h2>.*?</small>','<h2>나나 기본/포스 노바 · ARC 재추출</h2><small>각 줄: 기존 기본0 / 새 기본0 / 기존 포스15 / 새 포스15 / 기존5층 / 새5층. PL00의 실제 기본0·포스15를 유지하며 Ultimate 강제마스크 정책을 가져오지 않는다. 실제 EXE 원표106의 13스텝·유지시간·상대이동을 읽었다. 60호출/초는 검토 가정이며 이벤트80/40/20, 물리·입력·CLUT의 시간변화·실제 게임은 실행하지 않는다. 효과색은 고정 팔레트의 정적 비교다. 214는 새213+기존채택 원US외부124셀 효과이며 원US내부19셀까지 복원한 것은 아니다.216은 새215별칭,218/219는부모의별도에너지 그대로,220은새217 Y+1+효과다.</small>',html,flags=re.S)
 html=html.replace('section{display:flex;gap:4px}','section{display:flex;gap:4px;flex-wrap:wrap;max-width:2100px}')
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="160" height="96"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="320" height="192"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 for start in range(0,len(seq),4):
  chunk=seq[start:start+4];sheet=Image.new('RGB',(width*2*len(chunk),height*2*4+38),'#b6c0c7');dr=ImageDraw.Draw(sheet)
  for i,s in enumerate(chunk):
   n=s['ref'];x=i*width*2;dr.text((x+4,2),f'{n} / {s["calls"]}calls / step{s["step"]} / event{s["event"]:02X}',fill='black');dr.text((x+4,14),'OLD BASE / NEW BASE / OLD FOURTH / NEW FOURTH',fill='black')
   for j,(a,mask)in enumerate(((old,0),(new,0),(old,15),(new,15))):
    im=a.composite(n,mask)[0].crop(bounds).resize((width*2,height*2),Image.Resampling.NEAREST);sheet.paste(im,(x,38+j*height*2),im)
  sheet.save(out/f'timeline_106_{start//4+1}.png')
 write(out/'manifest.json',{'parent_arc_sha256':sha(old.data),'candidate_arc_sha256':sha(new.data),'exe_sha256':sha(exe),'source_bin':plan['source_bin'],'source_bin_sha256':plan['source_sha256'],'native_table_bytes_exact':True,'tables':[q],'cases':cases,'frames':frames,'window':bounds,'canvas_size':[width,height],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'clock_assumption':'60호출/초 검토 가정. 이벤트/caller/물리/CLUT변화 미실행.','changed_refs':[213,214,215,216,217,220],'scope':'원표106 13스텝/8참조48canvas. 준비213/215→217 전환과218~220 효과루프를 동일원점으로 정적·오프라인 재생한다. 실제 게임 관찰과 구분.'});print(json.dumps({'refs':len(REFS),'steps':len(seq),'canvas':48,'candidate':sha(new.data)}))
if __name__=='__main__':main()
