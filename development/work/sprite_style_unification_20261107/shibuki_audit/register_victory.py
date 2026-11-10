"""승리 원화를 동일 크기 셀의 고정 배율과 기존 두 CLUT으로 등록한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import sha,need,write
from register_ladder_detail import features

def main():
 p=argparse.ArgumentParser();p.add_argument('--page',type=int,choices=(1,2),required=True);p.add_argument('--source-sha',required=True);p.add_argument('--output',required=True);args=p.parse_args()
 folder=H/'victory_inputs01';source=folder/f'generated_page{args.page:02}.png';need(sha(source.read_bytes())==args.source_sha,'Source changed')
 im=Image.open(source).convert('RGBA');need(im.width==im.height and im.width%2==0,'Expected equal 2x2 grid');cell_size=im.width//2
 out=H/args.output;need(out.is_relative_to(H)and not out.exists(),'Output conflict');out.mkdir()
 data=(H/'prepared_ladder_wall_front02/PL00_U.ARC').read_bytes();need(sha(data)=='76f19a188ad58dd447eec058b669f8d62a4b8c00f957de3b229aeaa67f37495b','Parent changed');a=Archive(data)
 keys=[204,205]if args.page==1 else[206,207];rows=[];values={}
 for row,(form,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
  rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in struct.unpack_from('<16H',a.p,start*2)],np.int32);items=[]
  for col,n in enumerate(keys):
   cell=im.crop((col*cell_size,row*cell_size,(col+1)*cell_size,(row+1)*cell_size));v=quantize(cell,(64,64),rgb,128)
   q=np.zeros((384,384),np.uint8);q[128:192,128:192]=v;values[mask,n]=q
   Image.fromarray(q).save(out/f'{form}_{n:03}_indices.png');pic=a.rgba(q,start);pic.save(out/f'{form}_{n:03}.png')
   items.extend([(f'{n} old victory',a.composite(n,mask)[0]),(f'{n} new candidate',pic)])
   rows.append(dict(form=form,ref=n,new=features(q),old=features(a.layer(n)[0])if mask==0 else None))
  page(items,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
 write(out/'registration.json',dict(source_sha256=args.source_sha,source_dimensions=im.size,fixed_cell_scale=64/cell_size,native_origin=[160,160],rows=rows,source_overwrite=False,old_coarse_head_or_body_restored=False,pose_registration_pending=True,cross_costume_overlap=[dict(ref=n,base_outside_fourth=int(np.count_nonzero((values[0,n]>0)&(values[15,n]==0))))for n in keys],not_packed=True))
 print(json.dumps(dict(size=im.size,rows=rows)))
if __name__=='__main__':main()
