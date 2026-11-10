"""회복3의 실제 원화 홍채·원접지 정합. 187은 입증된186 표시 공유."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.prepare_rin_run import connected_groups
R=D/'rin_extension';A=R/'burst_recovery01';O=R/'burst_recovery_registered_v1';O.mkdir(exist_ok=False);read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();info=read(A/'inputs.json');arc=(ROOT/info['source_arc']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));source=np.array(Image.open(A/'generated.png').convert('RGBA'));targets={};rows=[];eyes={188:(146,162),189:(152,151)};moves={186:(0,1),188:(0,0),189:(0,1)}
for rec in info['masters']:
 n=rec['ref'];a=np.array(Image.open(A/'native_fixed'/f'b1_{n:03}_indices.png'));old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));ops=[]
 if n in eyes:
  x,y=eyes[n];cx,cy=rec['cell'];c=rec['world_crop'];sx=(x-c[0]+cx*96)*8;sy=(y-c[1]+cy*64)*8;p=source[sy:sy+8,sx:sx+8];r,g,b,al=[p[:,:,k].astype(int)for k in range(4)];m=(al>=128)&(g>r+15)&(b>r+15)&(g>70)&(g>b*.65);assert int(m.sum())==(18 if n==188 else 14);mean=p[m,:3].mean(0);assert mean[1]>mean[0]+80;ops.append({'world':[x,y],'source_sample_count':int(m.sum()),'source_sample_mean':mean.round(1).tolist(),'old_index':int(a[y,x]),'new_index':15,'reason':'원화에서 실제 존재하지만 셀 면적최빈색으로 소실된 작은 홍채'});a[y,x]=15
 dx,dy=moves[n];a=np.roll(np.roll(a,dy,0),dx,1);assert np.nonzero(a)[0].max()==np.nonzero(old)[0].max();assert len(connected_groups(a>0))==1;targets[n]=a;Image.fromarray(a).save(O/f'b1_{n:03}_body_indices.png');rows.append({'ref':n,'source_native_sha256':sha(A/'native_fixed'/f'b1_{n:03}_indices.png'),'source_eye_registration':ops,'whole_body_translation':[dx,dy],'target_sha256':sha(O/f'b1_{n:03}_body_indices.png'),'floor_y':int(np.nonzero(a)[0].max()),'connected_components':1})
assert np.array_equal(render(arc,1,5,186)[0],render(arc,1,5,187)[0]);Image.fromarray(targets[186]).save(O/'b1_187_body_indices.png')
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1440,1200),'#263142');dr=ImageDraw.Draw(sheet)
 for iy,n in enumerate(targets):
  for ix,(tag,a)in enumerate([('idle147',render(arc,0,0,147)[0]),('old body',render(arc,1,5,n)[0]),('new body',targets[n])]):
   pic=rgba(a,words).crop((112,112,208,188)).resize((480,380),Image.Resampling.NEAREST);sheet.paste(pic,(ix*480,iy*400+20),pic);dr.text((ix*480+4,iy*400+4),f'{n} {tag}',fill='white')
 sheet.save(O/f'{form}_comparison.png')
(O/'registration.json').write_text(json.dumps({'source_sha256':info['source_arc_sha256'],'generated_sha256':sha(A/'generated.png'),'records':rows,'aliases':{'187':186},'scope':'새원화 고정1/8과 실제 cyan눈2셀,186/189 접지y+1. 머리·몸체를 구형으로 덮지 않으며186/187 원래동일공유 유지.','runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(rows))
