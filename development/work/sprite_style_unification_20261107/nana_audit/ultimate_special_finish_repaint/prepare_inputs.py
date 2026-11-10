"""Ultimate95/98 두 독립 자세의 고정 원점 입력을 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC';need(digest(p)=='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0','동결 부모');a=Archive(p.read_bytes())
 bp=N.parent/'root_nana_special/packed_special02/PL00_U.ARC';need(digest(bp)=='f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648','수용 기본형 포즈');b=Archive(bp.read_bytes())
 out=D/'a_inputs_v1';out.mkdir(exist_ok=False);refs=[95,98];crop=(112,112,208,208);target=Image.new('RGBA',(1536,1536));style=target.copy();pose=Image.new('RGBA',(1536,768));frames=[]
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(refs):
   im=a.composite(n,mask)[0];target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));alpha=np.array(im)[:,:,3];alpha[112:208,112:208]=0;need(not alpha.any(),'고정 입력창')
   ref=0 if col==0 else 89;style.alpha_composite(a.composite(ref,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));frames.append({'ref':n,'form':form,'mask':mask,'cell':row*2+col,'source_rgba_sha256':sha(im.tobytes())})
 for col,n in enumerate(refs):pose.alpha_composite(b.composite(n)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,0))
 target.save(out/'targets.png');style.save(out/'style.png');pose.save(out/'accepted_pose_reference.png')
 write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'parent_frozen':True,'pose_reference_arc':bp.relative_to(ROOT).as_posix(),'pose_reference_sha256':digest(bp),'refs':refs,'columns':2,'rows':2,'native_cell':[96,96],'world_crop':[-48,-48,48,48],'frames':frames,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','accepted_pose_reference.png')],'scope':'별개 특수95/98 전신. 사다리 보류/거부 자료 사용 없음.96/99는 후속X+1 파생 정책 별도 검증.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
