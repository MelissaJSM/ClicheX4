"""새 등장원화의 실제 cyan 눈 표본을 팔레트 역할로 등록하고 발바닥을 정합한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.prepare_rin_run import connected_groups
R=Path(__file__).parent/'rin_extension';A=R/'arrival_detail01';N=A/'native_fixed';O=R/'arrival_contacts_probe_v1';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['source']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
eyes={249:[(155,142),(156,142)],250:[(155,142)],251:[(155,142)],252:[(152,143)],253:[(150,142)]};moves={249:(0,0),250:(0,0),251:(1,3),252:(0,3),253:(1,7)};data=json.loads((A/'contact_analysis/source_eye_cells.json').read_text('utf8'));targets={};records=[]
for n in range(249,254):
 a=np.array(Image.open(N/f'b0_{n:03}_indices.png'));old=render(arc,0,0,n)[0];samples=[]
 for x,y in eyes[n]:
  item=next(v for r in data['cyan_cells']if r['ref']==n for v in r['cyan_source_cells']if v['world']==[x,y]);assert item['count']>=20 and item['mean'][1]-item['mean'][0]>=60 and item['mean'][2]>item['mean'][0]+60;assert a[y,x]>0
  samples.append({**item,'old_quantized_index':int(a[y,x]),'new_index':15,'reason':'생성 원화에 실제 존재하는 청록색 홍채. 어두운 청록이 RGB 거리에서 남색으로 분류되던 손실을 역할팔레트로 등록.'});a[y,x]=15
 dx,dy=moves[n];a=np.roll(np.roll(a,dy,axis=0),dx,axis=1);assert np.where(a>0)[0].max()==np.where(old>0)[0].max();assert len(connected_groups(a>0))==1
 p=O/f'b0_{n:03}_indices.png';Image.fromarray(a).save(p);targets[n]=a
 yy,xx=np.nonzero(a);e=np.argwhere((a==15)&(np.indices(a.shape)[0]<160))[:,::-1];eo=np.argwhere((old==15)&(np.indices(a.shape)[0]<160))[:,::-1]
 records.append({'ref':n,'fixed_source':rel(N/f'b0_{n:03}_indices.png'),'fixed_source_sha256':sha(N/f'b0_{n:03}_indices.png'),'actual_source_eye_samples':samples,'whole_body_translation':[dx,dy],'output_sha256':sha(p),'eye_world':e.tolist(),'old_eye_world':eo.tolist(),'floor_y':int(yy.max()),'floor_x':np.where(a[yy.max()]>0)[0].tolist(),'bbox':rgba(a,pal).getbbox(),'old_head_override':False,'body_scale_change':False,'connected_components':1})
for form,words in [('normal',pal),('black',black)]:
 for page,ids in enumerate((list(range(249,252)),list(range(252,254)))):
  sh=Image.new('RGB',(1440,len(ids)*352),(28,34,45));dr=ImageDraw.Draw(sh)
  for i,n in enumerate(ids):
   for col,(label,v)in enumerate([('idle147',render(arc,0,0,147)[0]),(f'{n} old',render(arc,0,0,n)[0]),(f'{n} source eyes + floor',targets[n])]):
    pic=rgba(v,words).crop((112,120,208,184)).resize((480,320),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*352+28),pic);dr.text((col*480+8,i*352+7),label,fill='white')
  sh.save(O/f'{form}_comparison_{page:02}.png')
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':info['source_sha256'],'generated_sha256':sha(A/'generated.png'),'records':records,'scope':'새 원화의 실제 청록눈 표본 및 전신 정수이동만. 250눈+1y/253눈+2y 및 개별 발목/손 정합은 추가 검토 전이며 패킹후보 아님.','runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records,ensure_ascii=False))
