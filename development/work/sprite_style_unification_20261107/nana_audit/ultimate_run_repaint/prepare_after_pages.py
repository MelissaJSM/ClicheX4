"""채택된 새 이동 몸체의 의상 편집 입력. 기존 게임·원화 무수정."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,write,need
from make_body_review import GROUPS

def main():
 out=D/'after_inputs_v1';out.mkdir(exist_ok=False)
 src=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC'
 need(digest(src)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Frozen parent')
 a=Archive(src.read_bytes());window=(112,112,208,208);records=[]
 paths={n:D/group/f'before_{n:03}.png'for group,ns in GROUPS.items()for n in ns}
 paths[31]=D/'hand31_joint_probe_v1/before_031.png'
 for page,refs in zip(('a','b','c','d'),GROUPS.values()):
  sheet=Image.new('RGBA',(1536,1536));rows=[]
  for i,n in enumerate(refs):
   ar=np.array(Image.open(paths[n]));im=a.rgba(ar,16)
   alpha=np.array(im)[:,:,3].copy();alpha[112:208,112:208]=0;need(not alpha.any(),'No clipped pixels')
   sheet.alpha_composite(im.crop(window).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
   ys,xs=np.nonzero(ar);Y,X=np.indices(ar.shape);ey,ex=np.nonzero((ar==14)&(Y<165));top=int(ey.min())
   row={'ref':n,'cell':[i%2,i//2],'source':paths[n].relative_to(ROOT).as_posix(),'source_sha256':digest(paths[n]),'eye_world':[float(np.median(ex[ey==top])-160),top-160],'bbox_world':[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)]}
   rows.append(row);records.append(row)
  sheet.save(out/f'{page}_fixed_bodies.png');write(out/f'{page}_poses.json',rows)
 master=Image.new('RGBA',(1536,1536))
 for i,n in enumerate((0,39,65,71)):
  master.alpha_composite(a.composite(n,0)[0].crop(window).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
 master.save(out/'after_style_master.png')
 write(out/'manifest.json',{'parent_sha256':digest(src),'scope':'새 머리/눈/귀·손/권총·다리/신발·포즈/셀 원점은 유지하고 분홍 재킷만 기존 획득 후 의상으로 편집할 입력. 아직 원화/네이티브 최종물이 아님.','window':window,'cell_pixels':768,'native_scale':8,'records':records,'images':{p.name:digest(p)for p in out.glob('*.png')}})
 print(out)
if __name__=='__main__':main()
