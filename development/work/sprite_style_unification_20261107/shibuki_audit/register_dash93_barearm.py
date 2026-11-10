"""새 after93 앞팔만 재편집 원화에서 등록한다. 다른 모든 픽셀은 불변."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from probe_ultimate_dash_common01 import poly
ARM=[(-19,-12),(-14,-12),(-12,-9),(-12,-7),(-9,-5),(-8,-3),(-4,-2),(-4,1),(-9,0),(-11,-1),(-14,-3),(-17,-5),(-19,-8)]

def main():
    o=H/'ultimate_dash93_barearm_native02';need(not o.exists(),'Fresh native output');src=H/'ultimate_dash93_barearm01';p=src/'generated.png';need(sha(p.read_bytes())=='868f7d27fa21ae6dd58aca1444a8435ebafc8d9f2801442a03aeb06fd9d1cbe8','Source changed');im=Image.open(p).convert('RGBA');need(im.width==im.height and im.width>=512,'Wrong square canvas');o.mkdir()
    a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.int32);sample=np.array(im.resize((64,64),Image.Resampling.NEAREST));q=(1+((sample[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[sample[:,:,3]<128]=0;donor=np.zeros((384,384),np.uint8);donor[124:188,128:192]=q
    before=np.array(Image.open(H/'ultimate_dash_native04/after_093_indices.png'));mask=poly(ARM);y,x=np.indices(before.shape);match=(before>0)&~mask;tests=[]
    for dy in range(-2,3):
        for dx in range(-2,3):
            t=np.roll(np.roll(donor,dy,axis=0),dx,axis=1);tests.append({'shift':[dx,dy],'equal_opaque':int(np.count_nonzero((t==before)&match)),'alpha_diff':int(np.count_nonzero((t>0)!=(before>0)))})
    registered=donor;after=before.copy();after[mask]=registered[mask];need(np.array_equal(after[~mask],before[~mask]),'Unrelated region changed');changed=after!=before
    for name,v in(('source',before),('donor',donor),('after',after)):
        Image.fromarray(v).save(o/f'{name}_indices.png');a.rgba(v,0).save(o/f'{name}.png')
    Image.fromarray(mask.astype(np.uint8)*255).save(o/'arm_mask.png');Image.fromarray(changed.astype(np.uint8)*255).save(o/'changed_mask.png')
    page([('93 previous sleeve error',a.rgba(before,0)),('93 local bare arm candidate',a.rgba(after,0)),('93 full donor for registration only',a.rgba(donor,0))],a.composite(0,0)[0],o/'comparison.png',cols=3,scale=5)
    prompt=(src/'prompt.txt').read_text('utf8').strip();(src/'prompt_used.txt').write_text(prompt,encoding='utf8');write(src/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':'exec-035fbe27-3f25-466b-ba1d-f40519614385.png','source_sha256':sha(p.read_bytes()),'prompt_sha256':sha(prompt.encode()),'source_size':list(im.size),'native_cell':[64,64],'scale':64/im.width})
    write(o/'report.json',{'source_sha256':sha(p.read_bytes()),'source_size':list(im.size),'fixed_native_cell':[64,64],'native_scale':64/im.width,'arm_polygon':ARM,'donor_translation':[0,0],'registration_scores':tests,'changed_pixels':int(changed.sum()),'non_arm_exact':True,'source_arm_shape_only':True,'metrics_before':metrics(a.rgba(before,0)),'metrics_after':metrics(a.rgba(after,0)),'candidate_only':True,'visual_review_pending':True,'game_modified':False});print(json.dumps({'size':im.size,'changed':int(changed.sum()),'best':sorted(tests,key=lambda r:r['equal_opaque'],reverse=True)[:3]}))
if __name__=='__main__':main()
