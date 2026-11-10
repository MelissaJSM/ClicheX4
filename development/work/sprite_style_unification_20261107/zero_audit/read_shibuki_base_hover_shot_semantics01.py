"""피부 공통 선택식이 잡은 실제 팔레트색을 좌표별로 분리하는 보충읽기."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';O=D/'shibuki_base_hover_shots01';sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import color
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(R).as_posix()
report=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='0b98a7d07250b13ea7359c075ad8ea68e05bb50273d82e4d8f6b57886edc2961'
for p,h in report['inputs'].items():assert sha(R/p)==h,p
a=Archive((W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC').read_bytes());Y,X=np.indices((384,384));Y-=160;X-=160;rows=[];out=Image.new('RGB',(4*290,2*300),'#c8d0d5');dr=ImageDraw.Draw(out)
for rowi,n in enumerate((224,230)):
 r=next(q for q in report['frames']if q['ref']==n);base=np.array(Image.open(S/f'shot_registered01/base_legs_{n}_source_indices.png'));fourth=np.array(Image.open(S/f'shot_registered01/fourth_{n}_source_indices.png'));edit=np.array(Image.open(S/f'shot_composed01/edit_{n}.png'))>0
 selected=edit&(Y>=r['arm_bank7_min_y'])&(fourth==9)&~np.isin(base,(12,13))
 # 위 두 자세의 해당선택은 생성총제거창 밖이며 최종0에 실제남는지 확인한다.
 ls={pb:np.array(Image.open(S/f'shot_composed01/layer{pb}_{n}.png'))for pb in(0,5,6,7,8)};cells=[]
 for y,x in np.argwhere(selected):
  if not ls[0][y,x]==base[y,x] or any(ls[p][y,x]>0 for p in(5,6,7,8)):continue
  cells.append({'world':[int(x)-160,int(y)-160],'base_index':int(base[y,x]),'fourth_index':int(fourth[y,x]),'actual_common_RGBA':color(a,base)[y,x].tolist(),'source_fourth_RGBA':color(a,fourth,16)[y,x].tolist()})
 rows.append({'ref':n,'cells':cells,'finding':'Fourth의9번피부가OR선택을켜지만최종값은기본의빨강4/흰색9이다.선택셀수를모두피부픽셀로표기하면안된다.'})
 ims=[Image.fromarray(color(a,base)),Image.fromarray(color(a,fourth,16))]
 for mask in(8,15):
  z=color(a,ls[0])
  for bit,pb in((8,8),(1,5),(4,7),(2,6)):
   if mask&bit:q=color(a,ls[pb],16);m=q[:,:,3]>0;z[m]=q[m]
  ims.append(Image.fromarray(z))
 crop=(137,149,153,160)if n==224 else(148,152,160,166)
 for col,im in enumerate(ims):
  x0,y0=col*290,rowi*300;caption=['base donor','Fourth donor','composed mask8','composed mask15'][col];dr.text((x0+4,y0+4),f'{n} {caption}',fill='black');p=im.crop(crop).resize(((crop[2]-crop[0])*16,(crop[3]-crop[1])*16),Image.Resampling.NEAREST);out.paste(p,(x0+8,y0+32),p)
  for c in cells:
   x,y=c['world'];xx=x+160-crop[0];yy=y+160-crop[1];dr.rectangle((x0+8+xx*16,y0+32+yy*16,x0+8+xx*16+15,y0+32+yy*16+15),outline='#00a0bb',width=1)
  dr.text((x0+4,y0+270),'cyan box = selected common cell',fill='black')
assert sum(len(r['cells'])for r in rows)==3
p=O/'semantic_common_cells.png';assert not p.exists();out.save(p)
with(O/'semantic_common_cells.json').open('x',encoding='utf8')as f:json.dump({'scope':'기술일치와별개인공통피부명칭/의미범위진단','report_sha256':sha(O/'report.json'),'rows':rows,'image':{'path':rel(p),'sha256':sha(p)},'reader':{'path':rel(Path(__file__)),'sha256':sha(Path(__file__))},'candidate_changed':False,'art_decision':'손목그늘/칼라 출처로수용할지루트검토.수치만으로새색교체지시하지않음.'},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'rows':rows,'json_sha256':sha(O/'semantic_common_cells.json'),'image_sha256':sha(p)}))
