"""Ultimate 노바 준비의 새 공통머리/손발과 재킷층을 분리해 검사한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from probe_nova_layers import ARM,HANDS
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(160+x,160+y)for x,y in points],fill=1);return np.array(im,bool)
def main():
    d=H/'nova_ultimate_common01';need(not d.exists(),'새 공통후보');d.mkdir();a=Archive((H/'prepared_chaser_ultimate01/PL02_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype('uint8');rows=[];pics={'before':[],'after':[]}
    for n in (213,215):
        s=H/'nova_ultimate_footwear_composed01';before=np.array(Image.open(s/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(s/f'after_{n:03}_indices.png'));after=fresh.copy();arm=poly(ARM[n]);cut=8 if n==213 else -3
        head=((y<cut)&~arm)|((x>=9)&(y<(24 if n==213 else 18)))
        legs=(y>=(16 if n==213 else 12))
        if n==215:legs|=(y>=7)&(y<12)&(x>=-11)&(x<=3)&np.isin(before,[10,12,13])
        hand=np.logical_or.reduce([poly(ps)for ps in HANDS[n]])&np.isin(before,[10,12,13]);common=head|legs|hand;after[common]=lut[before][common]
        over=np.where(same_rgba(a,before,after),0,before).astype('uint8');layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}}
        outside=(after>0)&(before==0);delta=int(np.any(np.array(compose(a,layers,15))!=np.array(a.rgba(before,16)),axis=2).sum())
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        for name,m in [('head',head),('legs',legs),('hand',hand),('common',common),('outside_before',outside)]:Image.fromarray(m.astype('uint8')*255).save(d/f'{n:03}_{name}_mask.png')
        cc=[]
        for m in range(16):cc.append(int(label(np.array(compose(a,layers,m))[:,:,3]>0,np.ones((3,3)))[1]))
        for form,z,mask,pal in [('before',before,15,16),('after',after,0,0)]:
            Image.fromarray(z).save(d/f'{form}_{n:03}_indices.png');compose(a,layers,mask).save(d/f'{form}_{n:03}.png');pics[form].extend([(f'{n} 원화 국소 등록',Image.open(s/f'{form}_{n:03}.png')),(f'{n} 새 공통부',compose(a,layers,mask))])
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'before_composite_difference':delta,'unresolved_after_outside_before':[[int(px)-160,int(py)-160,int(after[py,px])]for py,px in zip(*np.nonzero(outside))],'common_opaque':int((common&(before>0)).sum()),'after_changed':int((after!=fresh).sum()),'partial_component_counts':cc,'rgba':{form:sha(compose(a,layers,mask).tobytes())for form,mask in [('before',15),('after',0)]}})
    for form,mask in [('before',15),('after',0)]:page(pics[form],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'rows':rows,'before16_to_after0':lut.tolist(),'arc_written':False,'final_acceptance':False,'policy':'새 before 머리/손발을 양쪽 의상에 공통 등록. 재킷 의미층5와 빈678을 실제 부모와 분기하며 기존 대상 밖 레코드는 보존 예정.'});print(json.dumps(rows))
if __name__=='__main__':main()
