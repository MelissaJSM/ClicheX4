"""별개83/94 두 자세와 확정 디테일 참조 두 셀을 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need
from prepare_inputs import SRC,EXPECTED,WINDOW,merged
def board(images):
 out=Image.new('RGBA',(1536,1536))
 for i,im in enumerate(images):out.alpha_composite(im.crop(WINDOW).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
 return out
def main():
 need(digest(SRC)==EXPECTED,'Parent');out=D/'last_inputs_v1';out.mkdir(exist_ok=False);a=Archive(SRC.read_bytes());p=D/'first_cases_probe_v2/before_067.png'
 board([a.composite(83,15)[0],a.composite(94,15)[0],a.composite(0,15)[0],a.rgba(np.array(Image.open(p)),16)]).save(out/'two_targets_two_masters.png')
 bpath=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';need(digest(bpath)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Basic source');b=Archive(bpath.read_bytes())
 board([b.composite(83,0)[0],b.composite(94,0)[0],a.composite(39,15)[0],a.composite(65,15)[0]]).save(out/'joint_and_detail_reference.png')
 records=[]
 for n in(83,94):
  old=merged(a,n,15);yy,xx=np.nonzero(old==14);ey=int(yy.min());ex=int(np.median(xx[yy==ey]));records.append({'ref':n,'native_eye_world':[ex-160,ey-160]})
 write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'refs':[83,94],'positions':records,'new67_sha256':digest(p),'source_base_arc_sha256':digest(bpath),'images':{p.name:digest(p)for p in out.glob('*.png')},'scope':'위2셀은별개83/94,아래2셀은변경하지않을대기·새67스타일참조.94는93복사가아닌별개몸체.'});print(out)
if __name__=='__main__':main()
