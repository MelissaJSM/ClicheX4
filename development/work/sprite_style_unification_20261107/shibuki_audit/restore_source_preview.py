"""기존 생성 원화 전체를 고정배율로 등록하는 읽기 전용 미술 실험."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from scipy.ndimage import label
from scripts.prepare_rin_run import quantize
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash
ART=ROOT/'work/ver_buki_riko/shibuki_art/ultimate_v1/production_art'
REFS=[33,39,55,65,204,207]
def foot(a):
 yy,xx=np.nonzero(a);bottom=int(yy.max());sx=np.nonzero((a>0)&(np.indices(a.shape)[0]>=bottom-1))[1]
 return int(round(float(np.median(sx)))),bottom
def main():
 assert file_hash(SOURCE)==SOURCE_SHA
 arc=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'])
 colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[17:32]],np.int32)
 groups=json.loads((ART/'master_groups.json').read_text());out=H/'source_restoration01';out.mkdir(exist_ok=False);meta=[]
 board=Image.new('RGB',(4*240,len(REFS)*240),(26,32,43));draw=ImageDraw.Draw(board)
 for row,n in enumerate(REFS):
  group=next(k for k,v in groups.items()if n in v);slot=groups[group].index(n);source=ART/f'{group}_generated.png';sheet=Image.open(source).convert('RGBA');w,h=sheet.size
  cut=sheet.crop((round(slot%4*w/4),round(slot//4*h/4),round((slot%4+1)*w/4),round((slot//4+1)*h/4)))
  z=np.array(cut);labs,num=label(z[:,:,3]>=200,np.ones((3,3),bool));cnt=np.bincount(labs.ravel());cnt[0]=0;mask=labs==int(cnt.argmax());z[:,:,3]=np.where(mask,z[:,:,3],0);cut=Image.fromarray(z)
  current=arc.composite(n,15)[0];anchor=foot(np.array(current)[:,:,3]);pictures=[('idle0',arc.composite(0,15)[0]),(f'{n} current',current)]
  for scale in (.20,.22):
   v=quantize(cut,colors,scale);sx,sy=foot(v);dx,dy=anchor[0]-sx,anchor[1]-sy;a=np.zeros((384,384),np.uint8);hh,ww=v.shape
   assert 0<=dx and 0<=dy and dx+ww<=384 and dy+hh<=384
   a[dy:dy+hh,dx:dx+ww]=v;im=arc.rgba(a,16);im.save(out/f'{n:03}_scale{int(scale*100)}.png');Image.fromarray(a).save(out/f'{n:03}_scale{int(scale*100)}_indices.png');pictures.append((f'full source scale{scale}',im))
   meta.append({'ref':n,'group':group,'source':source.relative_to(ROOT).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'cell':slot,'fixed_scale':scale,'translation':[dx,dy],'foot_anchor':anchor,'old_pixels_copied':0,'palette_start':16,'runtime_verified':False,'not_final_registration':True})
  for col,(text,im)in enumerate(pictures):
   draw.text((col*240+3,row*240+3),text,fill='white');pic=im.crop((120,120,200,190)).resize((240,210),Image.Resampling.NEAREST);board.paste(pic,(col*240,row*240+26),pic)
 board.save(out/'comparison.png');(out/'manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
if __name__=='__main__':main()
