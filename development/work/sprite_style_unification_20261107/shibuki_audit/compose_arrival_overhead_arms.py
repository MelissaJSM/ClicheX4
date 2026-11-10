"""새138/139 팔 donor만 의미영역으로 등록.그 밖의 새몸체는 바이트 수준 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from inspect_arrival_overhead_arms import grid

POLYGONS={
138:[[(-2,-29),(3,-29),(6,-25),(6,-6),(4,-2),(1,0),(-2,-1),(-2,-6),(-3,-9),(-3,-23),(-2,-25)], [(-8,-25),(-7,-28),(-3,-30),(1,-30),(2,-27),(-3,-24),(-5,-21),(-8,-22)]],
139:[[(-2,-30),(3,-30),(6,-26),(6,-6),(4,-2),(1,0),(-2,-1),(-2,-6),(-3,-9),(-3,-23),(-2,-25)], [(-8,-26),(-7,-29),(-3,-31),(1,-31),(2,-28),(-3,-25),(-5,-22),(-8,-23)]]}
def region(polys):
    im=Image.new('1',(384,384));d=ImageDraw.Draw(im)
    for points in polys:d.polygon([(x+160,y+160)for x,y in points],fill=1)
    return np.array(im,bool)
def main():
    out=H/'ultimate_arrival_overhead_arm_composed02';need(not out.exists(),'Fresh composition');out.mkdir();a=Archive((H/'prepared_ultimate_hurt02/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);rows=[];pics=[]
    for n,folder in((138,'ultimate_arrival_native02'),(139,'ultimate_arrival_separate_native01')):
        s=H/folder;b=np.array(Image.open(s/f'before_{n:03}_indices.png'));old=np.array(Image.open(s/f'after_{n:03}_indices.png'));donor=np.array(Image.open(H/f'ultimate_arrival_overhead_arm_inspection01/after_{n:03}_donor_indices.png'));mask=region(POLYGONS[n]);after=old.copy();after[mask]=donor[mask]
        # Restore the exact new-before clasp apex, not the old coarse body/arm.
        hand=np.zeros_like(mask);apex=-31 if n==138 else-32;hand[160+apex-1:160+apex+4,156:164]=True
        lower=np.zeros_like(mask);lower[160+apex+4:160+apex+7,156:165]=True;hand|=lower&np.isin(b,[10,11,12,13]);after[hand]=lut[b][hand];changed=after!=old
        need(np.array_equal(after[~(mask|hand)],old[~(mask|hand)]),'Non-arm source changed')
        for name,v,pal in(('before',b,16),('after',after,0)):
            Image.fromarray(v).save(out/f'{name}_{n:03}_indices.png');a.rgba(v,pal).save(out/f'{name}_{n:03}.png')
        for name,m in(('arm',mask),('new_clasp',hand),('changed',changed),('outside_before',(after>0)&(b==0))):Image.fromarray(m.astype(np.uint8)*255).save(out/f'{n:03}_{name}_mask.png')
        grid([a.rgba(b,16),a.rgba(old),a.rgba(after)],out/f'{n:03}_grid.png',[f'{n} new jacket protected',f'{n} previous sleeve rejected',f'{n} local bare arm candidate'])
        pics.extend([(f'{n} sleeve rejected',a.rgba(old)),(f'{n} local arm candidate',a.rgba(after))]);yy,xx=np.nonzero((after>0)&(b==0));lab,count=label(after>0,np.ones((3,3)));sizes=sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True)
        rows.append({'ref':n,'source_folder':folder,'source_hashes':{form:sha((s/f'{form}_{n:03}_indices.png').read_bytes())for form in('before','after')},'donor_array_sha256':sha(donor.tobytes()),'polygons':POLYGONS[n],'new_clasp_apex_y':apex,'changed_pixels':int(changed.sum()),'unmodified_outside_arm_and_new_clasp':True,'before_exact':True,'outside_before':[[int(x)-160,int(y)-160,int(after[y,x])]for y,x in zip(yy,xx)],'components_8way':int(count),'component_sizes':sizes,'before_metrics':metrics(a.rgba(b,16)),'after_metrics':metrics(a.rgba(after))})
    page(pics,a.composite(0,0)[0],out/'comparison.png',cols=2,scale=5)
    write(out/'report.json',{'rows':rows,'source_generated_sha256':'c33bd8ff574dca8a1b63dacfdcb9505d73be7e72e408c507b9420445ab53a15e','palette_map':lut.tolist(),'wholebody_rescale':False,'old_master_copy':False,'head_torso_legs_outside_local_arm_mask_exact':True,'ref135_included':False,'arc_written':False,'common_head_legs_alignment_pending':True,'visual_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
