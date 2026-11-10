"""기존 생성 원화의 디테일을 native 전체 그림으로 복원한 비교 후보. 게임 패킹 없음."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
from scripts.prepare_rin_run import quantize
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash
ART=ROOT/'work/ver_buki_riko/shibuki_art'
def clean(cut):
 z=np.array(cut.convert('RGBA'));labs,_=label(z[:,:,3]>=200,np.ones((3,3)));cnt=np.bincount(labs.ravel());cnt[0]=0;m=labs==cnt.argmax();z[:,:,3]=np.where(m,z[:,:,3],0);return Image.fromarray(z)
def foot(mask):
 yy,xx=np.nonzero(mask);y=int(yy.max());x=np.nonzero(mask&(np.indices(mask.shape)[0]>=y-1))[1];return int(round(float(np.median(x)))),y
def bbox(mask):
 y,x=np.nonzero(mask);return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]
def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);out=H/'remaining_source_restore01';out.mkdir(exist_ok=False);report=[]
 groups=json.loads((ART/'fourth_armor_remaining_v1/master_groups.json').read_text('utf8'))
 cases=[('base_lowhp',0,[120,122,124]),('fourth_wall',15,[55,57,59,65]),('fourth_rear',15,[144,151,156]),('fourth_action',15,[120,204,207])]
 for group,mask,refs in cases:
  items=[];palette_start=16 if mask else 0;rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[palette_start+1:palette_start+16]],np.int32)
  for n in refs:
   if not mask:
    source=ART/'low_hp_v1/generated.png';im=Image.open(source).convert('RGBA');i=[120,122,124].index(n);cut=clean(im.crop(([0,850,1390][i],0,[850,1390,im.width][i],im.height)));canonical=clean(im.crop((0,0,850,im.height)));page_id='low_hp';slot=i
   else:
    page_id=next(k for k,v in groups.items()if n in v);slot=groups[page_id].index(n);source=ART/f'fourth_armor_remaining_v1/{page_id}_generated.png';im=Image.open(source).convert('RGBA');w,h=im.size
    def cell(i):return clean(im.crop((round(i%4*w/4),round(i//4*h/4),round((i%4+1)*w/4),round((i//4+1)*h/4))))
    cut=cell(slot);cal={'air_dash':49,'action':120,'back_other':156}[page_id];canonical=cell(groups[page_id].index(cal))
   cb=bbox(np.array(canonical)[:,:,3]>=200);scale=47/(cb[3]-cb[1]);anchor=foot(np.array(a.composite(n,mask)[0])[:,:,3]>0);v=quantize(cut,rgb,scale);sx,sy=foot(v>0);dx,dy=anchor[0]-sx,anchor[1]-sy;full=np.zeros((384,384),np.uint8);full[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
   path=out/f'{group}_{n:03}_indices.png';Image.fromarray(full).save(path);new=a.rgba(full,palette_start);new.save(out/f'{group}_{n:03}.png')
   items.extend([(f'{n} current',a.composite(n,mask)[0]),(f'{n} whole source',new)])
   base_alpha=np.array(a.composite(n,0)[0])[:,:,3]>0
   report.append({'form':'fourth'if mask else'base','ref':n,'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_cell':slot,'canonical_source_height':cb[3]-cb[1],'uniform_scale':scale,'translation':[dx,dy],'foot_anchor':anchor,'old_head_or_body_copied':False,'current_base_alpha_not_covered_by_new_full':int(np.count_nonzero(base_alpha&(full==0)))if mask else None,'not_registered_to_game':True,'hand_contact_not_presumed':True})
  page(items,a.composite(0,mask)[0],out/f'{group}.png',cols=2,scale=4)
 (out/'manifest.json').write_text(json.dumps({'source_bin_sha256':SOURCE_SHA,'scope':'미술 비교 후보. 기존 원화 전체를 등방 축소하고 접지만 맞춤. 원작 다른 접점은 미검증.','records':report},ensure_ascii=False,indent=2)+'\n','utf8')
if __name__=='__main__':main()
