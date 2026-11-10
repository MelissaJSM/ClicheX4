"""후반벽 새 두상/다리 고정 후 팔·목의 국소 재작화만 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page,metrics
from register_ultimate_lowhp_pilot import move,sole
I=H/'ultimate_wall_raised_edit01';O=H/'ultimate_wall_raised_native01';P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
def skin_tip(q):
    Y,X=np.indices(q.shape);yy,xx=np.nonzero(np.isin(q,[12,13])&(Y<144)&(X>166));need(len(xx)>0,'No raised palm');top=yy.min();return int(round(float(xx[yy<=top+1].mean()))),int(top)
def filled(q):
    m=np.zeros_like(q,bool)
    for y,row in enumerate(q):
        xs=np.flatnonzero(row)
        if len(xs):m[y,xs.min():xs.max()+1]=True
    return m
def main():
    need(not O.exists(),'Fresh output required');need(sha((I/'generated.png').read_bytes())=='6007926194bb10a4a0d7b96931512d04a622d299bb28ca2746a5bb7996835804','Unexpected art');a=Archive(P.read_bytes());info=json.loads((I/'inputs.json').read_text('utf8'));im=Image.open(I/'generated.png').convert('RGBA');need(im.width==3*im.height,'Unexpected page');pix=np.array(im.resize((192,64),Image.Resampling.NEAREST));colors=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[16:32]],np.int32)
    idx=(1+((pix[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[pix[:,:,3]<128]=0;O.mkdir();rows=[];outputs={}
    for i,n in enumerate((61,63,65)):
        r=next(v for v in info['rows']if v['ref']==n);guide=np.array(Image.open(I/f'{n:03}_pose_guide_indices.png'));source=np.zeros_like(guide);source[120:184,128:192]=idx[:,i*64:(i+1)*64]
        palm=np.array(Image.open(I/f'{n:03}_hand_module.png'));palm=move(palm,*r['hand_translation']);head=np.array(Image.open(I/f'{n:03}_head_module.png'));head=move(head,*r['head_module_translation']);ht=skin_tip(palm);gt=skin_tip(source);dx,dy=ht[0]-gt[0],ht[1]-gt[1];authored=move(source,dx,dy)
        mm=Image.new('1',(384,384));d=ImageDraw.Draw(mm);poly=[(8,-32),(25,-32),(25,-3),(15,0),(6,-2),(4,-8),(6,-14)];d.polygon([(x+160,y+160)for x,y in poly],fill=1);d.rectangle((157,151,169,161),fill=1);mask=np.array(mm,bool)
        output=guide.copy();output[mask]=authored[mask];headmask=filled(head);handmask=filled(palm);output[headmask]=head[headmask];output[handmask]=palm[handmask];outputs[n]=output
        source_before=np.array(Image.open(H/'ultimate_wall_page02_native01'/f'{n:03}_indices.png'))
        need(np.array_equal(output[177:],source_before[177:]),'Foot moved');need(sole(output)==sole(source_before),'Ground center moved')
        for label,q in [('indices',output),('authored',authored),('edit_mask',mask.astype(np.uint8)*255),('head_mask',headmask.astype(np.uint8)*255),('hand_mask',handmask.astype(np.uint8)*255)]:Image.fromarray(q).save(O/f'{n:03}_{label}.png')
        a.rgba(output,16).save(O/f'{n:03}.png')
        rows.append({'ref':n,'new_source_arm_translation':[dx,dy],'head_module_translation':r['head_module_translation'],'palm_tip_world':[x-160 for x in ht],'palm_pixels_exact_to_guide':bool(np.array_equal(output[handmask],palm[handmask])),'new_head_pixels_exact_to_guide':bool(np.array_equal(output[headmask],head[headmask])),'new_head_pixels':int(np.count_nonzero(head)),'new_upper_arm_neck_pixels':int(np.count_nonzero(mask&~headmask&~handmask)),'other_guide_pixels_exact':bool(np.array_equal(output[~(mask|headmask|handmask)],guide[~(mask|headmask|handmask)])),'feet_exact':True,'original_pose_metrics':metrics(a.composite(n,15)[0]),'new_metrics':metrics(a.rgba(output,16)),'candidate_only':True})
    page([(f'{n} old pose',a.composite(n,15)[0])for n in(61,63,65)]+[(f'{n} new connected arm',a.rgba(outputs[n],16))for n in(61,63,65)],a.composite(0,15)[0],O/'comparison.png',cols=3,scale=6)
    page([(f'{n} first new body',Image.open(H/'ultimate_wall_contacts_probe01/before'/f'{n:03}.png'))for n in(55,57,59)]+[(f'{n} after arm alignment',a.rgba(outputs[n],16))for n in(61,63,65)],a.composite(0,15)[0],O/'six_comparison.png',cols=3,scale=6)
    sheet=Image.new('RGBA',(1536,512))
    for i,n in enumerate((61,63,65)):sheet.alpha_composite(a.rgba(outputs[n],16).crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
    sheet.save(O/'after_edit_target.png');write(O/'registration.json',{'source_sha256':sha((I/'generated.png').read_bytes()),'source_dimensions':im.size,'fixed_page_native':[192,64],'whole_source_scale':192/im.width,'rows':rows,'old_head_body_pixels_copied':0,'body_bbox_resize':False,'palette_changed':False,'packed':False,'accepted':False})
    info['generated']=True;info['generated_sha256']=sha((I/'generated.png').read_bytes());info['native_registration']=str(O.relative_to(ROOT));write(I/'inputs.json',info);print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
