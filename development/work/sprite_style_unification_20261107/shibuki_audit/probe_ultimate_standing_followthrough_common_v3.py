"""새90/91 공통부와 새 donor 팔꿈치 외곽2셀의 양폼 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent
ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from probe_ultimate_standing_followthrough_common import HEAD,FRONT,poly

def main():
    d=H/'ultimate_standing_followthrough_common03'
    need(not d.exists(),'새 후보 폴더 필요')
    a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes())
    s=H/'ultimate_standing_followthrough_native02'
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)] for w in a.words],np.int32)
    lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype('uint8')
    y=np.indices((384,384))[0]-160
    d.mkdir(); rows=[]; pics={'before':[],'after':[]}
    for n in (90,91):
        original_before=np.array(Image.open(s/f'before_{n:03}_indices.png'))
        before=original_before.copy()
        fresh=np.array(Image.open(s/f'after_{n:03}_indices.png')); after=fresh.copy()
        guard=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png'))>0
        front=poly(FRONT[n])&~guard
        gun=np.where(guard,a.layer(n,0)[0],0).astype('uint8')
        head=poly(HEAD[n])&~front&~guard; legs=(y>=11)&(y<25)
        common=(head|legs)&~front&~guard
        after[common]=lut[before][common]
        before[guard]=gun[guard]; after[guard]=gun[guard]
        shared_elbow=[]
        if n==90:
            for cx,cy in [(-13,-4),(-12,-3)]:
                iy,ix=cy+160,cx+160
                need(before[iy,ix]==0 and after[iy,ix]==fresh[iy,ix]==15,'새 donor 외곽 출처 변경')
                need(front[iy,ix] and not guard[iy,ix],'팔꿈치 범위')
                need(a.words[15]==a.words[31],'양폼 같은 그늘 색')
                before[iy,ix]=after[iy,ix]
                shared_elbow.append([cx,cy,15])
        outside=(after>0)&(before==0)
        need(not outside.any(),'후폼 외곽 누출')
        over=np.where(same_rgba(a,before,after),0,before).astype('uint8'); over[guard]=0
        layers={0:after,5:over,**{b:np.zeros_like(after) for b in(6,7,8)}}
        expected=np.array(a.rgba(before,16)); expected[guard]=np.array(a.rgba(gun))[guard]
        need(compose(a,layers,15).tobytes()==expected.tobytes(),'전폼 RGBA 불일치')
        need(compose(a,layers,0).tobytes()==a.rgba(after).tobytes(),'후폼 RGBA 불일치')
        contact={}
        for form,v,mask in [('before',before,15),('after',after,0)]:
            im=compose(a,layers,mask)
            Image.fromarray(v).save(d/f'{form}_{n:03}_indices.png'); im.save(d/f'{form}_{n:03}.png')
            pics[form].extend([(f'{n} 새 등록',Image.open(s/f'{form}_{n:03}.png')),(f'{n} 공통부/총',im)])
            lab,_=label(v>0,np.ones((3,3)))
            adj=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard&front
            contact[form]={'components8':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'front_arm_fourway_gun_contact':[[int(cx)-160,int(cy)-160] for cy,cx in zip(*np.nonzero(adj))],'metrics':metrics(im)}
        for name,m in [('common',common),('head',head),('legs',legs),('front_arm',front),('gun_guard',guard),('outside',outside)]:
            Image.fromarray(m.astype('uint8')*255).save(d/f'{n:03}_{name}_mask.png')
        for b,v in layers.items(): Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(gun).save(d/f'{n:03}_gun_indices.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m)) for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        checks=all(np.array_equal(np.array(compose(a,layers,m))[guard],np.array(a.rgba(gun))[guard]) for m in range(16))
        need(checks,'부분폼 총열 불일치')
        rows.append({'ref':n,'head_polygon':HEAD[n],'front_arm_polygon':FRONT[n],'common_legs_y':[11,25],'shared_elbow_new_donor_shadow':shared_elbow,'before_changed_outside_gun':int(((before!=original_before)&~guard).sum()),'shared_elbow_policy':'새 맨팔 donor 보라 외곽을 같은 관절의 재킷 외곽에도 공동 등록. 다른 소매나 기존 몸체 복사/임의 색 채움 없음.','before_rgba_exact':True,'after_rgba_exact':True,'outside_before':[],'common_opaque':int(((before>0)&common).sum()),'after_common_changed':int((after!=fresh).sum()),'gun_opaque':int((gun>0).sum()),'gun_transparent_guard':int((guard&(gun==0)).sum()),'gun_policy':'기본형과 같은 의미영역에서 현재 PL02 after 실제 총 색인을 읽음. 옛 소매/귀 제외.','gun_before_palette0_override':True,'gun_checks16':checks,'contact':contact,'old_head_copied':False,'global_body_scale':False})
    for form,mask in [('before',15),('after',0)]: page(pics[form],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=6)
    write(d/'report.json',{'parent_sha256':sha(a.data),'native_report_sha256':sha((s/'report.json').read_bytes()),'palette16_to0':lut.tolist(),'rows':rows,'all_sources_retained':True,'diagnostic_only':False,'arc_written':False,'contacts_and_partial_review_pending':True})
    print(json.dumps(rows))
if __name__=='__main__': main()
