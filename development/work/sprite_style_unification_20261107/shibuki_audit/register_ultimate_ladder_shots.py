"""새 발사팔만 고정96셀 등록. 새149 머리/몸과 정본총열은 정확 보존."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from probe_ultimate_ladder_common import poly
def main():
    o=H/'ultimate_ladder_shots_registered01';need(not o.exists(),'Fresh output');o.mkdir();s=H/'ultimate_ladder_shot_inputs01';src=s/'generated.png';need(sha(src.read_bytes())=='c09b3ef9ed78d5d971c5889a13771cbb7228af8975ff8518d2643fa0000e9c37','Art changed');im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Fixed page changed');sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));a=Archive((H/'prepared_ultimate_dash01/PL02_U.ARC').read_bytes());head=np.array(Image.open(H/'ultimate_ladder_common_probe02/149_head_mask.png'))>0;legs=np.array(Image.open(H/'ultimate_ladder_common_probe02/149_legs_mask.png'))>0;rows=[];pics={'before':[],'after':[]}
    for col,(n,(mx,my))in enumerate([(150,(-24,-9)),(155,(-21,-13))]):
        guard=np.array(Image.open(s/f'{n:03}_barrel_mask.png'))>0;gun=np.array(Image.open(s/f'{n:03}_barrel_indices.png'));oldarm=poly([(-16,-7),(-6,-8),(-2,-2),(-3,8),(-13,8),(-16,2)]);newarm=poly([(mx+6,my-4),(-5,-10),(-1,-1),(-2,7),(-13,8),(mx+6,my+7)]);edit=(oldarm|newarm)&~head&~legs&~guard;values={}
        for row,(form,pal,mask)in enumerate([('before',16,15),('after',0,0)]):
            bodypath=H/f'ultimate_ladder_contacts01/{form}_149_indices.png';body=np.array(Image.open(bodypath));rgb=np.array([[(int(w)>>ss&31)*255//31 for ss in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);c=sample[row*64:(row+1)*64,col*96:(col+1)*96];q=(1+((c[:,:,:3].astype('int32')[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2)).astype('uint8');q[c[:,:,3]<128]=0;donor=np.zeros_like(body);donor[128:192,112:208]=q;v=body.copy();v[edit]=donor[edit];v[guard]=gun[guard];need(np.array_equal(v[~(edit|guard)],body[~(edit|guard)]),'Nonlocal body changed');need(np.array_equal(v[guard],gun[guard]),'Barrel changed');values[form]=v
            Image.fromarray(donor).save(o/f'{form}_{n:03}_source_indices.png');Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');Image.fromarray(edit.astype('uint8')*255).save(o/f'{n:03}_edit_mask.png');rgba=a.rgba(v,pal);rgba.save(o/f'{form}_{n:03}.png');pics[form].extend([(f'{n} old {form}',a.composite(n,mask)[0]),(f'{n} new arm {form}',rgba)]);rows.append({'ref':n,'form':form,'body_ref':149,'body_sha256':sha(bodypath.read_bytes()),'palette_start':pal,'new_arm_changed_pixels':int(np.count_nonzero((v!=body)&edit)),'nonlocal_body_exact':True,'canonical_barrel_raw_exact':True,'master_barrel_opaque':60,'master_barrel_transparent':11,'whole_body_rescale':False,'source_scale':0.125,'alpha_threshold':128,'head_new_body_preserved':True})
        outside=(values['after']>0)&(values['before']==0);points=[[int(x-160),int(y-160),int(values['after'][y,x])]for y,x in zip(*np.nonzero(outside))];Image.fromarray(outside.astype('uint8')*255).save(o/f'{n:03}_outside_mask.png')
        for r in rows:
            if r['ref']==n:r['outside_after_points']=points
    for form,mask in [('before',15),('after',0)]:page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=6)
    write(o/'report.json',{'source_sha256':sha(src.read_bytes()),'source_input_sha256':sha((s/'input.json').read_bytes()),'parent_sha256':sha(a.data),'rows':rows,'scope':'새149 수용 제작구조에팔만등록한후보.원US155 전체몸체와동일복원이라는뜻아님.','native_source_frozen':False,'needs_visual_and_common_alpha_review':True,'arc_written':False,'runtime_verified':False});write(s/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':'exec-fb9f1a0a-da9c-4224-b856-d5bcb960875e.png','sha256':sha(src.read_bytes()),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'input_images':{f:sha((s/f).read_bytes())for f in('edit_target.png','arm_guide.png')},'original_preserved':True});print(json.dumps([{'ref':r['ref'],'form':r['form'],'arm':r['new_arm_changed_pixels'],'outside':len(r['outside_after_points'])}for r in rows]))
if __name__=='__main__':main()
