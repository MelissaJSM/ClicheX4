"""새86/87/92의 공통 머리·사지와 실제 총열 정합 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from probe_ultimate_standing_fire_common import poly
HEAD={n:[(-24,-28),(16,-28),(16,7),(11,7),(8,4),(7,-1),(4,-4),(-6,-4),(-8,-5),(-24,-5)]for n in(86,87,92)}
FRONT={86:[(-12,-6),(-7,-6),(-7,-4),(-5,-4),(-5,-2),(-3,-2),(-3,3),(-9,3),(-12,-1)],87:[(-14,-8),(-8,-8),(-8,-5),(-7,-5),(-7,2),(-6,2),(-6,4),(-11,4),(-14,1)],92:[(-12,-4),(-7,-4),(-5,-2),(-4,1),(-5,6),(-10,6),(-12,2)]}

def main():
    d=H/'ultimate_standing_recovery_common01';need(not d.exists(),'새 후보 필요');d.mkdir()
    s=H/'ultimate_standing_recovery_native01';a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words],np.int32)
    lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype('uint8')
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics={'before':[],'after':[]}
    for n in(86,87,92):
        before=np.array(Image.open(s/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(s/f'after_{n:03}_indices.png'));after=fresh.copy()
        guard=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png'))>0
        front=poly(FRONT[n])&~guard
        if n==86:
            gun=np.roll(np.array(Image.open(H/'ultimate_dash_barrel_guard01/master_indices.png')),(2,6),(0,1))
            need((gun>0).sum()==60 and guard.sum()==71,'정본34 범위')
        else:gun=np.where(guard,a.layer(n,0)[0],0).astype('uint8')
        head=poly(HEAD[n])&~front&~guard;legs=(y>=11)&(y<25);hand=(x>=6)&(x<=13)&(y>=7)&(y<=11)
        common=(head|legs|hand)&~front&~guard;after[common]=lut[before][common]
        before[guard]=gun[guard];after[guard]=gun[guard]
        outside=(after>0)&(before==0);over=np.where(same_rgba(a,before,after),0,before).astype('uint8');over[guard]=0
        layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}}
        expected=np.array(a.rgba(before,16));expected[guard]=np.array(a.rgba(gun))[guard]
        exact=compose(a,layers,15).tobytes()==expected.tobytes();contact={}
        for form,v,mask in [('before',before,15),('after',after,0)]:
            im=compose(a,layers,mask);Image.fromarray(v).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png')
            pics[form].extend([(f'{n} 새 원화',Image.open(s/f'{form}_{n:03}.png')),(f'{n} 공통부/총',im)])
            lab,_=label(v>0,np.ones((3,3)));adj=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard&front
            contact[form]={'components8':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'gun_contact4':[[int(cx)-160,int(cy)-160]for cy,cx in zip(*np.nonzero(adj))],'metrics':metrics(im)}
        for name,m in [('common',common),('head',head),('legs',legs),('lower_hand',hand),('front_arm',front),('gun_guard',guard),('outside',outside)]:Image.fromarray(m.astype('uint8')*255).save(d/f'{n:03}_{name}_mask.png')
        for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(gun).save(d/f'{n:03}_gun_indices.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'head_polygon':HEAD[n],'front_arm_polygon':FRONT[n],'legs_y':[11,25],'lower_hand_box':[6,7,13,11],'before_rgba_exact':exact,'outside_before':[[int(cx)-160,int(cy)-160,int(after[cy,cx])]for cy,cx in zip(*np.nonzero(outside))],'after_common_changed':int((after!=fresh).sum()),'gun_opaque':int((gun>0).sum()),'gun_transparent_guard':int((guard&(gun==0)).sum()),'gun_palette0_override_for_before':True,'gun_checks16':all(np.array_equal(np.array(compose(a,layers,m))[guard],np.array(a.rgba(gun))[guard])for m in range(16)),'contact':contact,'old_head_copied':False,'body_scaled':False})
    for form,mask in [('before',15),('after',0)]:page(pics[form],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'native_report_sha256':sha((s/'report.json').read_bytes()),'palette16_to0':lut.tolist(),'rows':rows,'diagnostic_only':not all(r['before_rgba_exact']for r in rows),'arc_written':False,'contacts_review_pending':True})
    print(json.dumps(rows))
if __name__=='__main__':main()
