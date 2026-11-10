"""140 착지 전후의 원표2 발췌와 caller에서 확인한 부분마스크 전환을 보여준다."""
from pathlib import Path
import sys,json,io,base64,ast,re
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from scripts.export_sprite_playback import read_disc,at
BEFORE='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3'
FINAL='2822a9387a69119e6a3f6ba0f3cc830676280309b139494221940e0e9a005c59'

def main():
 out=D/'native_cycle_v1';need(not out.exists(),'새 순서판');out.mkdir()
 old=Archive((N/'base_nova_repaint/packed_nova_candidate_v1/PL00_U.ARC').read_bytes());new=Archive((D/'packed_flash_candidate_v1/PL00_U.ARC').read_bytes());need(sha(old.data)==BEFORE and sha(new.data)==FINAL,'고정 자원')
 plan=json.loads((D/'native_components_v1.json').read_text('utf8'));src=ROOT/plan['source_bin'];need(digest(src)==plan['source_sha256'],'RN42 원본');exe=read_disc(src,['SLUS_005.61'])['SLUS_005.61']
 caller=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_base_effect_callers01/conclusions.json';cj=json.loads(caller.read_text('utf8'));need(sha(exe)==cj['source_EXE_sha256'],'caller 조사와 EXE 동일')
 meta=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));q=next(z for z in meta['characters']['nana']['forms']['base']['animations']if z['id']==2)
 need(at(exe,int(q['table_address'],16)+8,4).hex()==q['pointer_bytes'],'원표 포인터')
 for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'원표 스텝')
 steps=q['steps'][12:];need([s['frame_ref']for s in steps]==[138,139,140,141,142,142],'착지 발췌')
 need(steps[2]['event']==1 and steps[2]['duration_calls']==3,'140 event1')
 seq=[{'ref':s['frame_ref'],'calls':s['duration_calls'],'step':s['relative_step'],'event':s['event'],'original_position':s['position']}for s in steps];cases={'2 tail positions12-17':seq};bounds=(112,112,208,208);width=height=96;data={};frames=[]
 for n in range(138,143):
  fourth_mask=0 if n<140 else 15
  ims=[old.composite(n,0)[0],new.composite(n,0)[0],old.composite(n,fourth_mask)[0],new.composite(n,fourth_mask)[0],new.composite(0,0)[0],new.composite(0,15)[0]];urls=[];hashes=[]
  for j,im in enumerate(ims):
   outside=np.array(im)[:,:,3];outside[bounds[1]:bounds[3],bounds[0]:bounds[2]]=0;need(not outside.any(),'검토창 절단')
   crop=im.crop(bounds);crop.save(out/f'{n:03}_{j}.png');buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode());v=np.array(crop);v[v[:,:,3]==0]=0;hashes.append(sha(v.tobytes()))
  data[str(n)]=urls;frames.append({'ref':n,'fourth_mask_from_caller':fourth_mask,'canvas_rgba_sha256':hashes})
 tree=ast.parse((N/'ultimate_wall_repaint/make_native_cycle.py').read_text('utf8'));html=next(z.value.value for z in ast.walk(tree)if isinstance(z,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='html'for t in z.targets)and isinstance(z.value,ast.Constant))
 html=html.replace('Nana Ultimate native wall review','Nana landing flash140 review')
 text='각 줄: 기존 기본 / 새 기본 / 기존 포스 / 새 포스 / 기준 기본 대기 / 기준 포스 대기. 원표2의 position12~17만 발췌한 착지138→139→140→141→142 순서다. 포스도138/139는일시마스크0이며140 event1 처리 뒤 같은업데이트에서 복구된마스크15를 표시한다는 실제caller 읽기 근거를 적용했다. 이 도구가 caller 자체를 실행한 것은 아니다. 140은3호출,142 끝96/상대0은 검토용 반복이며 실제 게임의 종료·복귀 시간으로 주장하지 않는다. 60호출/초는 검토 가정이고 고정팔레트·동일원점의 오프라인 비교이며 실제물리·클루트변화·실기 검증은 별도다. 새140은 현 대기의 부분 의상 알파149셀만 같은 빛색으로 추가했다. 기본형/원46효과와208~212 분신 자원은 보존했다.'
 html=re.sub(r'<h2>.*?</small>','<h2>나나 착지 섬광140 · 최종ARC 원순서 발췌</h2><small>'+text+'</small>',html,flags=re.S)
 html=html.replace('SMALL',''.join(f'<canvas id="small{j}" width="96" height="96"></canvas>'for j in range(6))).replace('BIG',''.join(f'<canvas id="big{j}" width="288" height="288"></canvas>'for j in range(6))).replace('DATAJSON',json.dumps(data,separators=(',',':'))).replace('CASEJSON',json.dumps(cases,separators=(',',':')));(out/'REVIEW.html').write_text(html,'utf8')
 sheet=Image.new('RGB',(width*3*5,height*3*4+44),'#b6c0c7');dr=ImageDraw.Draw(sheet)
 for i,n in enumerate(range(138,143)):
  s=steps[i];mask=0 if n<140 else 15;x=i*width*3;dr.text((x+5,3),f'{n}: {s["duration_calls"]}calls / event{s["event"]} / Fourth mask{mask}',fill='black');dr.text((x+5,20),'OLD BASE / NEW BASE / OLD FOURTH / NEW FOURTH',fill='black')
  for j,(a,m)in enumerate(((old,0),(new,0),(old,mask),(new,mask))):
   im=a.composite(n,m)[0].crop(bounds).resize((width*3,height*3),Image.Resampling.NEAREST);sheet.paste(im,(x,44+j*height*3),im)
 sheet.save(out/'timeline_2_landing.png')
 write(out/'manifest.json',{'parent_arc_sha256':BEFORE,'candidate_arc_sha256':FINAL,'exe_sha256':sha(exe),'source_bin':plan['source_bin'],'source_bin_sha256':plan['source_sha256'],'caller_evidence':{'path':caller.relative_to(ROOT).as_posix(),'sha256':digest(caller)},'native_table_bytes_exact':True,'tables':[q],'cases':cases,'frames':frames,'window':bounds,'canvas_size':[96,96],'html_sha256':digest(out/'REVIEW.html'),'runtime_verified':False,'scope':'원표2의18스텝바이트검증/마지막6스텝5참조30canvas. 실제caller읽기에서 확인한138139 mask0→140 event1 mask15를 그림합성에적용. caller/물리/실제게임실행아님.','terminal_policy':'끝142/96/relative0은검토반복만,실제시간주장없음.'});print(json.dumps({'refs':5,'steps':6,'canvas':30,'candidate':FINAL}))
if __name__=='__main__':main()
