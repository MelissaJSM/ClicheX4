"""새 등장 원화를 전체페이지 고정 배율과 기존 CLUT으로만 등록한다."""
from pathlib import Path
import sys,struct,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import need,sha,write
from register_ladder_detail import features

def main():
 out=H/'arrival_native01';need(not out.exists(),'Output exists');out.mkdir();d=H/'arrival_inputs01'
 data=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();need(sha(data)=='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf','Parent changed');a=Archive(data)
 sources=[('generated_page01.png',2,[(0,133,0),(1,135,0)]),('generated_page02.png',3,[(0,137,0),(1,138,0)]),('generated_fourth_sleeve.png',3,[(2,138,15)])]
 rows=[];sources_meta=[];pictures={};imgs={0:[],15:[]}
 for filename,cols,targets in sources:
  source=d/filename;im=Image.open(source).convert('RGBA');nativew=cols*64;nativeh=round(im.height/(im.width/nativew));need(nativeh==64,'Generated sheet aspect changed')
  for start in sorted({16 if mask else 0 for cell,n,mask in targets}):
   rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in struct.unpack_from('<16H',a.p,start*2)],np.int32)
   indexed=quantize(im,(nativew,64),rgb,128)
   for cell,n,mask in targets:
    if start!=(16 if mask else 0):continue
    q=np.zeros((384,384),np.uint8);q[128:192,128:192]=indexed[:,cell*64:(cell+1)*64];form='fourth'if mask else'base'
    Image.fromarray(q).save(out/f'{form}_{n:03}_indices.png');pic=a.rgba(q,start);pic.save(out/f'{form}_{n:03}.png');pictures[mask,n]=q
    imgs[mask].extend([(f'{n} current',a.composite(n,mask)[0]),(f'{n} fixed-scale candidate',pic)])
    rows.append(dict(form=form,ref=n,source=filename,cell=cell,source_sha256=sha(source.read_bytes()),new=features(q),old=features(a.layer(n)[0])if mask==0 else None))
  sources_meta.append(dict(source=filename,sha256=sha(source.read_bytes()),dimensions=im.size,native_size=[nativew,64],uniform_scale=nativew/im.width))
 for mask,name in((0,'base'),(15,'fourth')):page(imgs[mask],a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=5)
 write(out/'registration.json',dict(source_arc_sha256=sha(data),sources=sources_meta,rows=rows,native_origin=[160,160],old_coarse_body_head_restored=False,whole_body_or_limb_resize=False,contacts_review_pending=True,base_outside_fourth_138=int(np.count_nonzero((pictures[0,138]>0)&(pictures[15,138]==0))),not_packed=True))
 print(json.dumps(dict(rows=rows,overlap=int(np.count_nonzero((pictures[0,138]>0)&(pictures[15,138]==0))))))
if __name__=='__main__':main()
