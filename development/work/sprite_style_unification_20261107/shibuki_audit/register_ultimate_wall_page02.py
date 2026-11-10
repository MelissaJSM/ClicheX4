"""남은 벽3자세의 새 재킷형을 전체 페이지 고정축척으로 등록한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from register_ultimate_lowhp_pilot import sole,move
P=H/'prepared_ultimate_lowhp01/PL02_U.ARC';I=H/'ultimate_wall_inputs01/page02_generated_before.png';O=H/'ultimate_wall_page02_native01'
def main():
    need(not O.exists(),'Fresh registration directory required');need(sha(I.read_bytes())=='fe53d3955ab64b2d636c1ad6ec96245024c3da861e2713f1f2b3bf8119a35c8c','Source changed');need(sha(P.read_bytes())=='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b','Parent changed')
    a=Archive(P.read_bytes());im=Image.open(I).convert('RGBA');need(im.width==im.height*3,'Unexpected ratio');sample=np.array(im.resize((192,64),Image.Resampling.NEAREST));colors=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[16:32]],np.int32)
    idx=(1+((sample[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);idx[sample[:,:,3]<128]=0
    O.mkdir();rows=[];items=[];views={}
    for i,n in enumerate((61,63,65)):
        q=np.zeros((384,384),np.uint8);q[120:184,128:192]=idx[:,i*64:(i+1)*64];old=a.composite(n,15)[0];target=sole(np.array(old.getchannel('A')));current=sole(q);dx,dy=target[0]-current[0],target[1]-current[1];v=move(q,dx,dy)
        Image.fromarray(q).save(O/f'{n:03}_unregistered_indices.png');Image.fromarray(v).save(O/f'{n:03}_indices.png');a.rgba(v,16).save(O/f'{n:03}.png');views[n]=a.rgba(v,16)
        rows.append({'ref':n,'translation':[dx,dy],'old_metrics':metrics(old),'new_metrics':metrics(views[n]),'source_sole_world':[x-160 for x in target],'new_sole_world':[x-160 for x in sole(v)],'old_pose_copied':False,'head_and_wall_hand_pending':True})
    page([(f'{n} current',a.composite(n,15)[0])for n in(61,63,65)]+[(f'{n} new',views[n])for n in(61,63,65)],a.composite(0,15)[0],O/'comparison.png',cols=3,scale=6)
    page([(f'{n} first page',Image.open(H/'ultimate_wall_contacts_probe01/before'/f'{n:03}.png'))for n in(55,57,59)]+[(f'{n} second page',views[n])for n in(61,63,65)],a.composite(0,15)[0],O/'six_body_comparison.png',cols=3,scale=6)
    sheet=Image.new('RGBA',(1536,512))
    for i,n in enumerate((61,63,65)):sheet.alpha_composite(views[n].crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
    sheet.save(O/'after_edit_target.png')
    write(O/'registration.json',{'source':str(I.relative_to(ROOT)),'source_sha256':sha(I.read_bytes()),'source_dimensions':im.size,'native_page':[192,64],'scale':192/im.width,'parent_sha256':sha(P.read_bytes()),'palette_start':16,'individual_bbox_resize':False,'rows':rows,'packed':False,'candidate_only':True})
    print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
