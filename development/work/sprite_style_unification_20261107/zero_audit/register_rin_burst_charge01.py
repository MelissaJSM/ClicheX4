"""원화 cyan 표본과 발바닥을 정합하고 원구체와 함께 손 접점을 검토한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.prepare_rin_run import connected_groups
R=D/'rin_extension';A=R/'burst_charge01';O=R/'burst_charge_registered_v1';O.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();info=read(A/'inputs.json');arc=(ROOT/info['source_arc']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));samples=read(A/'contact_analysis/cyan_samples.json');targets={};rows=[]
eyes={178:(152,145),180:(156,144)};moves={178:(0,1),179:(0,1),180:(0,1),181:(0,0)}
for rec in info['masters']:
 n=rec['ref'];a=np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png'));old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));ops=[]
 if n in eyes:
  x,y=eyes[n];s=next(s for r in samples if r['ref']==n for s in r['cyan_cells']if s['world']==[x,y]);assert s['count']>=30 and s['mean'][1]>s['mean'][0]+80;ops.append({**s,'old_index':int(a[y,x]),'new_index':15,'reason':'생성 원화 실제 청록 홍채의 역할팔레트 등록'});a[y,x]=15
 dx,dy=moves[n];a=np.roll(np.roll(a,dy,0),dx,1);assert np.nonzero(a)[0].max()==np.nonzero(old)[0].max();assert len(connected_groups(a>0))==1;targets[n]=a;Image.fromarray(a).save(O/f'b1_{n:03}_body_indices.png');fx=np.array(Image.open(R/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png'));v=a.copy();v[fx>0]=fx[fx>0];Image.fromarray(v).save(O/f'b1_{n:03}_combined_indices.png')
 rows.append({'ref':n,'source_native_sha256':sha(A/'native_fixed'/f'b1_{n:03}_indices.png'),'source_eye_registration':ops,'whole_body_translation':[dx,dy],'target_sha256':sha(O/f'b1_{n:03}_body_indices.png'),'effect_pixels':int(np.count_nonzero(fx)),'effect_over_new_body_pixels':int(np.count_nonzero((fx>0)&(a>0))),'floor_y':int(np.nonzero(a)[0].max()),'connected_components':1})
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1440,len(rows)*400),'#263142');effects=Image.new('RGB',(1440,len(rows)*400),'#263142');dr=ImageDraw.Draw(sheet);de=ImageDraw.Draw(effects)
 for iy,n in enumerate(targets):
  oldbody=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));newbody=targets[n];fx=np.array(Image.open(R/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png'));combined=newbody.copy();combined[fx>0]=fx[fx>0]
  for canvas,draw,cases in [(sheet,dr,[('idle147',render(arc,0,0,147)[0]),('old body',oldbody),('new body',newbody)]),(effects,de,[('old combined',render(arc,1,5,n)[0]),('new combined',combined),('new body',newbody)])]:
   for ix,(tag,a)in enumerate(cases):
    pic=rgba(a,words).crop((112,112,208,188)).resize((480,380),Image.Resampling.NEAREST);canvas.paste(pic,(ix*480,iy*400+20),pic);draw.text((ix*480+4,iy*400+4),f'{n} {tag}',fill='white')
 sheet.save(O/f'{form}_comparison.png');effects.save(O/f'{form}_effects.png')
(O/'registration.json').write_text(json.dumps({'source_sha256':info['source_arc_sha256'],'generated_sha256':sha(A/'generated.png'),'records':rows,'scope':'고정1/8 원화에 실제 cyan표본2셀과 전신y+1 접지만 등록한 후보. 구체는부모원좌표/원색exact이며 손목접점 최종열람 전.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
