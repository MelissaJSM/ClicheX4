"""신작90/91의 공통머리·다리와 독립분리 총열 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from register_ultimate_standing90_arm import POLY
HEAD={90:[(-25,-27),(16,-27),(16,9),(10,9),(8,5),(7,1),(3,-3),(-7,-3),(-10,-4),(-25,-4)],91:[(-21,-27),(16,-27),(16,9),(10,9),(8,4),(5,-2),(-6,-4),(-21,-4)]}
FRONT={90:POLY,91:[(-19,-5),(-13,-5),(-9,-3),(-6,-3),(-4,-1),(-6,3),(-14,3),(-18,1),(-19,-2)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main():
    d=H/'ultimate_standing_followthrough_common02';need(not d.exists(),'새 후보 폴더');d.mkdir();a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());s=H/'ultimate_standing_followthrough_native02';rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype('uint8');yy,xx=np.indices((384,384));y=yy-160;rows=[];pics={'before':[],'after':[]}
    for n in(90,91):
        before=np.array(Image.open(s/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(s/f'after_{n:03}_indices.png'));after=fresh.copy();guard=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png'))>0;front=poly(FRONT[n])&~guard;gun=np.where(guard,a.layer(n,0)[0],0).astype('uint8');head=poly(HEAD[n])&~front&~guard;legs=(y>=11)&(y<25);common=(head|legs)&~front&~guard
        after[common]=lut[before][common];before[guard]=gun[guard];after[guard]=gun[guard];outside=(after>0)&(before==0);over=np.where(same_rgba(a,before,after),0,before).astype('uint8');over[guard]=0;layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}}
        expected=np.array(a.rgba(before,16));expected[guard]=np.array(a.rgba(gun))[guard];before_exact=compose(a,layers,15).tobytes()==expected.tobytes();contact={}
        for form,v,mask in [('before',before,15),('after',after,0)]:
            im=compose(a,layers,mask);Image.fromarray(v).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');pics[form].extend([(f'{n} 팔등록',Image.open(s/f'{form}_{n:03}.png')),(f'{n} 공통/총',im)]);lab,_=label(v>0,np.ones((3,3)));adj=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard&front
            contact[form]={'components8':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'front_arm_fourway_gun_contact':[[int(cx)-160,int(cy)-160]for cy,cx in zip(*np.nonzero(adj))],'metrics':metrics(im)}
        for name,m in [('common',common),('head',head),('legs',legs),('front_arm',front),('gun_guard',guard),('outside',outside)]:Image.fromarray(m.astype('uint8')*255).save(d/f'{n:03}_{name}_mask.png')
        for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(gun).save(d/f'{n:03}_gun_indices.png');page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'head_polygon':HEAD[n],'front_arm_polygon':FRONT[n],'common_legs_y':[11,25],'before_rgba_exact':before_exact,'outside_before':[[int(cx)-160,int(cy)-160,int(after[cy,cx])]for cy,cx in zip(*np.nonzero(outside))],'common_opaque':int(((before>0)&common).sum()),'after_common_changed':int((after!=fresh).sum()),'gun_opaque':int((gun>0).sum()),'gun_transparent_guard':int((guard&(gun==0)).sum()),'gun_policy':'기본형에서분리한동일좌표의미영역을 현재PL02after 실제색인으로읽음.뒤소매는제외.','gun_before_palette0_override':True,'gun_checks16':all(np.array_equal(np.array(compose(a,layers,m))[guard],np.array(a.rgba(gun))[guard])for m in range(16)),'contact':contact,'old_head_copied':False,'global_body_scale':False})
    for form,mask in [('before',15),('after',0)]:page(pics[form],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=6)
    write(d/'report.json',{'parent_sha256':sha(a.data),'native_report_sha256':sha((s/'report.json').read_bytes()),'palette16_to0':lut.tolist(),'rows':rows,'all_sources_retained':True,'diagnostic_only':not all(r['before_rgba_exact']for r in rows),'arc_written':False,'contacts_and_partial_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
