"""새 얼티밋 벽3자세를 페이지 고정 축척으로 읽는다. 등록 후보이며 패킹하지 않는다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page,metrics
from register_ultimate_lowhp_pilot import sole,move
P=H/'prepared_ultimate_lowhp01/PL02_U.ARC';I=H/'ultimate_wall_inputs01';O=H/'ultimate_wall_native01'
SOURCES={'before':'9613107a60a23d01bd50ac60102bf0716bcbfb3373818ad1e0f6468082cec8d7','after':'bc1b3492c7f3e23d1e26a68087b3cad685fc8fcbeaa73fe00486a5ee11bcac24'}
PATHS={form:I/f'page01_generated_{form}.png'for form in SOURCES}
UPDATE_INPUT_INFO=True
def main():
    need(not O.exists(),'Fresh registration output required');need(sha(P.read_bytes())=='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b','Unexpected parent')
    a=Archive(P.read_bytes());O.mkdir();rows=[];targets={};sources={}
    for form,start,mask in [('before',16,15),('after',0,0)]:
        p=PATHS[form];need(sha(p.read_bytes())==SOURCES[form],'Source art changed')
        im=Image.open(p).convert('RGBA');need(im.width==im.height*3,'Invalid page ratio')
        sample=np.array(im.resize((192,64),Image.Resampling.NEAREST));sources[form]={'path':str(p.relative_to(ROOT)),'sha256':SOURCES[form],'dimensions':im.size,'fixed_uniform_scale':192/im.width}
        colors=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[start:start+16]],np.int32)
        (O/form).mkdir();targets[form]={}
        for col,n in enumerate([55,57,59]):
            rgb=sample[:,col*64:(col+1)*64];d=((rgb[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3)
            q=(d.argmin(2)+1).astype(np.uint8);q[rgb[:,:,3]<128]=0
            raw=np.zeros((384,384),np.uint8);raw[120:184,128:192]=q
            old=a.composite(n,mask)[0];oldalpha=np.array(old.getchannel('A'))
            original_sole=sole(oldalpha);desired=original_sole if form=='before' else sole(targets['before'][n])
            sx,sy=sole(raw);dx,dy=desired[0]-sx,desired[1]-sy;v=move(raw,dx,dy);targets[form][n]=v
            Image.fromarray(raw).save(O/form/f'{n:03}_unregistered_indices.png');Image.fromarray(v).save(O/form/f'{n:03}_indices.png');a.rgba(v,start).save(O/form/f'{n:03}.png')
            rows.append({'form':form,'ref':n,'palette_start':start,'translation':[dx,dy],'old_sole_world':[x-160 for x in original_sole],'registered_sole_world':[x-160 for x in sole(v)],'before_sole_exact':sole(v)==desired,'old':metrics(old),'new':metrics(a.rgba(v,start)),'head_contact_check_pending':True,'not_frozen':True})
        page([(f'{n} current',a.composite(n,mask)[0])for n in(55,57,59)]+[(f'{n} new',a.rgba(targets[form][n],start))for n in(55,57,59)],a.composite(0,mask)[0],O/f'{form}_comparison.png',cols=3,scale=6)
    outside={}
    for n in(55,57,59):
        diff=(targets['after'][n]>0)&(targets['before'][n]==0);outside[str(n)]=int(diff.sum());Image.fromarray(diff.astype(np.uint8)*255).save(O/f'{n}_outside_after.png')
    board=Image.new('RGBA',(1536,1024))
    for r,(form,start)in enumerate([('before',16),('after',0)]):
        for c,n in enumerate([55,57,59]):board.alpha_composite(a.rgba(targets[form][n],start).crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(c*512,r*512))
    board.save(O/'pair.png')
    write(O/'registration.json',{'parent_sha256':sha(P.read_bytes()),'sources':sources,'page_native_size':[192,64],'source_reference_viewport_world':[-32,-40,32,24],'rows':rows,'after_outside_before_pixels':outside,'old_head_or_body_copied':False,'bbox_resize':False,'palette_changed':False,'packed':False,'accepted':False,'limitations':['첫 고정축척 등록이다. 머리 크기, 손·발 접점과 양폼 공통 부분 정합은 다음 검사에서 확정한다.','발바닥 중심의 평행이동만 했고 관절 사이를 늘리거나 원본 머리로 덮지 않았다.']})
    if UPDATE_INPUT_INFO:
        sourceinfo=json.loads((I/'manifest.json').read_text('utf8'))
        for r in sourceinfo['refs']:r['native_body_world_bbox']=[v-160 for v in a.composite(r['body_ref'],15)[0].getbbox()]
        sourceinfo.update({'generation_started':True,'first_page_before_completed':True,'first_page_after_completed':True,'generated_sources':sources,'game_written':False})
        write(I/'manifest.json',sourceinfo)
    print(json.dumps({'out':str(O),'outside':outside,'poses':rows},ensure_ascii=False))
if __name__=='__main__':main()
