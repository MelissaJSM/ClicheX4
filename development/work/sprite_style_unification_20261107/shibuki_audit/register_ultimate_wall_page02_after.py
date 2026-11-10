"""새 민소매 후반 벽 원화를 고정 축척/발 접점으로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from register_ultimate_lowhp_pilot import move,sole

I=H/'ultimate_wall_page02_after01';B=H/'ultimate_wall_raised_native01';O=H/'ultimate_wall_page02_after_native01'
S='f3baf9b3e367e149cbe881151c0d8ff2a9e39c2ea88934b82745219b79852a59'

def main():
    need(not O.exists() and sha((I/'generated.png').read_bytes())==S,'Fresh output / fixed source required')
    a=Archive((H/'prepared_ultimate_lowhp01/PL02_U.ARC').read_bytes());im=Image.open(I/'generated.png').convert('RGBA')
    need(im.width==im.height*3,'Unexpected layout');pix=np.array(im.resize((192,64),Image.Resampling.NEAREST))
    colors=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[:16]],np.int32)
    idx=(1+((pix[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[pix[:,:,3]<128]=0
    O.mkdir();targets={};rows=[]
    for col,n in enumerate((61,63,65)):
        before=np.array(Image.open(B/f'{n:03}_indices.png'));q=np.zeros((384,384),np.uint8);q[120:184,128:192]=idx[:,col*64:(col+1)*64]
        anchor=sole(before);sx,sy=sole(q);dx,dy=anchor[0]-sx,anchor[1]-sy;after=move(q,dx,dy);targets[n]=after
        Image.fromarray(q).save(O/f'{n:03}_unregistered_indices.png');Image.fromarray(after).save(O/f'{n:03}_indices.png');a.rgba(after).save(O/f'{n:03}.png')
        outside=(after>0)&(before==0);Image.fromarray(outside.astype(np.uint8)*255).save(O/f'{n:03}_outside.png')
        rows.append({'ref':n,'translation':[dx,dy],'new_after':metrics(a.rgba(after)),'before':metrics(a.rgba(before,16)),'after_outside_before':int(outside.sum()),'body_bbox_resize':False,'sole_anchor_exact':sole(after)==anchor})
    page([(f'{n} before',a.rgba(np.array(Image.open(B/f'{n:03}_indices.png')),16))for n in targets]+[(f'{n} new after, raw registration',a.rgba(q))for n,q in targets.items()],a.composite(0,0)[0],O/'comparison.png',cols=3,scale=6)
    write(O/'registration.json',{'source_sha256':S,'source_dimensions':im.size,'native_fixed_page':[192,64],'rows':rows,'packed':False,'candidate_only':True,'next':'새 머리/손/발 동일 모듈을 유지하며 새 의상과 팔의 목점 정합. 원화 전체를 잘라 넣거나 옛 몸을 쓰지 않는다.'})
    info=json.loads((I/'inputs.json').read_text('utf8'));info.update({'generated':True,'generated_sha256':S,'native_registration':str(O.relative_to(ROOT))});write(I/'inputs.json',info)
    print(rows)

if __name__=='__main__':main()
