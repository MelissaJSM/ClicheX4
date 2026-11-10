"""노바 기존 몸체와 대시73의 정확한 좌표 관계를 읽기 조사한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
SRC=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC'
def main():
 a=Archive(SRC.read_bytes());need(sha(a.data)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Parent');out=D/'nova_head_source_audit_v2';out.mkdir(exist_ok=False);old=a.layer(73)[0];labs,num=label(old>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;body=np.where(labs==sizes.argmax(),old,0).astype(np.uint8);ys,xs=np.nonzero(body);rows=[];proof=[]
 for n in(217,218,219,220):
  ar=a.layer(n)[0];y,x=np.nonzero(ar);dx=int(x.min()-xs.min())if len(x)else 0;dy=int(y.min()-ys.min())if len(y)else 0;shift=np.roll(body,(dy,dx),(0,1));eq=np.array_equal(shift,ar);proof.append({'ref':n,'translation':[dx,dy],'old73_body_translation_exact':eq,'different_texels':int(np.count_nonzero(shift!=ar)),'tile_count':a.banks[0]['frames'][n]['tile_count']});rows.append((str(n),[('old73 base',a.rgba(body)),('nova base',a.rgba(ar)),('nova overlay5',a.rgba(a.layer(n,5)[0],16)),('nova full',a.composite(n,15)[0])]))
 helper.grid(rows,out/'comparison.png',5)
 new=np.array(Image.open(D/'joint_native_targets_v1/after_071.png'));font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',10)
 for name,ar in(('old73body',body),('new71',new)):
  im=a.rgba(ar).crop((130,140,195,188)).resize((65*18,48*18),Image.Resampling.NEAREST).convert('RGB');dr=ImageDraw.Draw(im)
  for yy in range(48):
   for xx in range(65):
    val=int(ar[140+yy,130+xx]);dr.text((xx*18+3,yy*18+3),format(val,'x')if val else'.',font=font,fill=(0,0,0)if val in(4,8,9,11,14)else(255,255,255))
  im.save(out/f'{name}_grid.png');Image.fromarray(ar).save(out/f'{name}.png')
 write(out/'report.json',{'parent_sha256':sha(a.data),'frames':proof,'old_body_index_sha256':sha(body.tobytes()),'new_source':(D/'joint_native_targets_v1/after_071.png').relative_to(ROOT).as_posix(),'new_source_sha256':digest(D/'joint_native_targets_v1/after_071.png'),'read_only':True});print(json.dumps(proof))
if __name__=='__main__':main()
