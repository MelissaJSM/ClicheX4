"""새85/89의 공통머리·사지와 폼공통 총열을 정합하는 독립 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from register_ultimate_standing_arms import POLYS
HEAD={85:[(-21,-27),(15,-27),(15,6),(11,6),(9,3),(8,-2),(5,-4),(-6,-4),(-7,-5),(-21,-5)],89:[(-21,-27),(15,-27),(15,8),(10,8),(8,5),(7,1),(4,-3),(-7,-3),(-9,-5),(-21,-5)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main():
    d=H/'ultimate_standing_fire_common01';need(not d.exists(),'새 공통층 후보 필요');d.mkdir();a=Archive((H/'prepared_standing_special_ultimate01/PL02_U.ARC').read_bytes());src=H/'ultimate_standing_fire_native02';rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype('uint8');yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics={'before':[],'after':[]}
    for n in(85,89):
        before=np.array(Image.open(src/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(src/f'after_{n:03}_indices.png'));after=fresh.copy();front=poly(POLYS[n]);guard=np.array(Image.open(H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png'))>0
        if n==85:
            gun=np.roll(np.array(Image.open(H/'ultimate_dash_barrel_guard01/master_indices.png')),(2,5),(0,1));need(int((gun>0).sum())==60 and int(guard.sum())==71,'정본34 범위');policy='수용PL02 after34 총열60+11를 (+5,+2) 평행등록. 옛85 총열변형 보존 주장이 아님.'
        else:
            old=a.layer(n,0)[0];gun=np.where(guard,old,0).astype('uint8');need(int((gun>0).sum())==54,'89원총열 영역');policy='현재PL02 after89의 행별 의미총열54와투명가드11.기본형 독립분리한 귀제외 영역을같은원좌표로읽음.옛before와4셀 RGBA차이는공통after총열로통일.'
        head=poly(HEAD[n])&~front&~guard;legs=(y>=11)&(y<25);hand=(x>=6)&(x<=13)&(y>=7)&(y<=11);common=(head|legs|hand)&~front&~guard;after[common]=lut[before][common];before[guard]=gun[guard];after[guard]=gun[guard]
        outside=(after>0)&(before==0);over=np.where(same_rgba(a,before,after),0,before).astype('uint8');over[guard]=0;layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}}
        expected=np.array(a.rgba(before,16));expected[guard]=np.array(a.rgba(gun))[guard];need(compose(a,layers,15).tobytes()==expected.tobytes(),'재킷RGBA출처 불일치')
        body_contact={}
        for form,v,mask,pal in [('before',before,15,16),('after',after,0,0)]:
            im=compose(a,layers,mask);Image.fromarray(v).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');pics[form].extend([(f'{n} new native',Image.open(src/f'{form}_{n:03}.png')),(f'{n} common/canonical',im)]);contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard&front;lab,_=label(v>0,np.ones((3,3)));body_contact[form]={'fourway_front_arm_contact':[[int(cx)-160,int(cy)-160]for cy,cx in zip(*np.nonzero(contact))],'components8':sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True),'metrics':metrics(im)}
        for name,m in [('common',common),('head',head),('legs',legs),('lower_hand',hand),('front_arm',front),('gun_guard',guard),('outside',outside)]:Image.fromarray(m.astype('uint8')*255).save(d/f'{n:03}_{name}_mask.png')
        Image.fromarray(gun).save(d/f'{n:03}_gun_indices.png');a.rgba(gun).save(d/f'{n:03}_gun.png')
        for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        olddiff={str(m):int((guard&np.any(np.array(a.composite(n,m)[0])!=np.array(a.rgba(gun)),axis=2)).sum())for m in(0,15)}
        rows.append({'ref':n,'head_polygon':HEAD[n],'front_arm_polygon':POLYS[n],'legs_y':[11,25],'lower_hand_box':[6,7,13,11],'new_common_opaque':int(((before>0)&common).sum()),'new_after_common_changes':int((after!=fresh).sum()),'outside_before':[[int(cx)-160,int(cy)-160,int(after[cy,cx])]for cy,cx in zip(*np.nonzero(outside))],'gun_policy':policy,'gun_old_rgba_delta':olddiff,'gun_palette0_override_for_before':True,'gun_checks_all16':all(np.array_equal(np.array(compose(a,layers,m))[guard],np.array(a.rgba(gun))[guard])for m in range(16)),'body_contact':body_contact,'old_head_body_copied':False,'body_scaled':False})
    for form,mask in [('before',15),('after',0)]:page(pics[form],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=6)
    write(d/'report.json',{'parent_sha256':sha(a.data),'native_report_sha256':sha((src/'report.json').read_bytes()),'before16_to_after0':lut.tolist(),'rows':rows,'target_layers_candidate':10,'new_gun_hand_contact_and_contour_review_pending':True,'arc_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
