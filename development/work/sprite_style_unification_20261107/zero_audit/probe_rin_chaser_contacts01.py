"""새 체이서 원화의 눈/신발을 정수 평행이동만으로 원접점에 맞추는 후보."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import connected_groups
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=Path(__file__).parent/'rin_extension';A=R/'chaser_detail01';N=A/'native_fixed';O=R/'chaser_contacts_probe_v1';assert not O.exists();O.mkdir()
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['source']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();refs=[14,22,30,38]
# New source-only lower leg regions. These leave the skin knee and upper skirt intact.
polys={22:[(171,162),(182,162),(182,176),(174,176),(174,169),(171,167)],30:[(169,165),(181,165),(181,180),(170,180),(170,171),(168,168)],38:[(163,168),(178,168),(178,185),(162,185),(159,173)]}
records=[];targets={}
for n in refs:
 v=np.array(Image.open(N/f'b1_{n:03}_indices.png'));old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));a=v.copy();ops=[]
 if n==22:
  p=[(139,137),(164,137),(164,152),(158,152),(158,154),(153,154),(153,155),(145,155),(139,152)]
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(p,fill=1);mask=np.array(mask)&(a>0);layer=np.where(mask,a,0).astype(np.uint8);a[mask]=0;mov=np.roll(layer,1,axis=0);occluded=int(np.count_nonzero((mov>0)&(a>0)));a[mov>0]=mov[mov>0];ops.append({'region':'new_head_only','polygon':p,'translation':[0,1],'source_pixels':int(mask.sum()),'new_source_joint_overlap_pixels':occluded})
 if n in polys:
  mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(polys[n],fill=1);mask=np.array(mask)&(a>0);layer=np.where(mask,a,0).astype(np.uint8);a[mask]=0;mov=np.roll(layer,1,axis=0);occluded=int(np.count_nonzero((mov>0)&(a>0)));a[mov>0]=mov[mov>0];ops.append({'region':'new_boot_only','polygon':polys[n],'translation':[0,1],'source_pixels':int(mask.sum()),'new_source_joint_overlap_pixels':occluded})
 assert int(np.where(a>0)[0].max())==int(np.where(old>0)[0].max());assert len(connected_groups(a>0))==1,(n,[len(g)for g in connected_groups(a>0)])
 eye=np.argwhere((a==15)&(np.indices(a.shape)[0]<160))[:,::-1];oldeye=np.argwhere((old==15)&(np.indices(a.shape)[0]<160))[:,::-1];assert np.array_equal(eye,oldeye)
 p=O/f'b1_{n:03}_body_indices.png';Image.fromarray(a).save(p);targets[n]=a;records.append({'ref':n,'source_sha256':sha(N/f'b1_{n:03}_indices.png'),'output_sha256':sha(p),'operations':ops,'eye_exact':True,'floor_y_exact':True,'connected_components':1,'old_pixels_pasted':0,'invented_colors':0})
for form,words in [('normal',pal),('black',black)]:
 sh=Image.new('RGB',(1920,4*352),(28,34,45));dr=ImageDraw.Draw(sh)
 for i,n in enumerate(refs):
  old=np.array(Image.open(A/f'b1_{n:03}_body_indices.png'));raw=np.array(Image.open(N/f'b1_{n:03}_indices.png'));tail=np.array(Image.open(A/f'b1_{n:03}_ribbon_indices.png'));full=np.where(targets[n],targets[n],tail).astype(np.uint8)
  for col,(label,v)in enumerate([('old',old),('new fixed',raw),('new contacts',targets[n]),('original ribbon+new',full)]):
   pic=rgba(v,words).crop((112,120,208,184)).resize((480,320),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*352+28),pic);dr.text((col*480+8,i*352+7),f'{n} {label}',fill='white')
 sh.save(O/f'{form}_comparison.png')
j={'source_arc_sha256':info['source_sha256'],'generated_sha256':sha(A/'generated.png'),'records':records,'scope':'새 원화 고정1/8 후22머리+1y와22/30/38신발+1y 정수이동만 시험. 원래 눈/발바닥 일치, 손/상체와 구형머리 덮기 없음. 아직 채택/패킹 아님.','runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
