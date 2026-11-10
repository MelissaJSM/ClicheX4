"""새 Ultimate 체이서의 공통머리/사지와 재킷 소유 후보를 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
SOURCES={162:'chaser_ultimate_contacts01',166:'chaser_ultimate_contacts01',170:'chaser_ultimate_native02',174:'chaser_ultimate_native02'}
HEAD_CUT={162:-3,166:-1,170:-1,174:0}
BRAID={162:(8,3),166:(8,4),170:(8,7),174:(6,8)}
HAND={162:[(-9,-1),(-6,-1),(-6,1),(-9,1)],166:[(-9,2),(-6,2),(-6,3),(-9,3)],170:[(-10,2),(-6,2),(-6,5),(-10,5)],174:[(-10,1),(-6,1),(-6,5),(-10,5)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(160+x,160+y)for x,y in points],fill=1);return np.array(im,bool)
def main():
    d=H/'chaser_ultimate_common01';need(not d.exists(),'새 공통후보 필요');d.mkdir();a=Archive((H/'prepared_standing_fire_ultimate01/PL02_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype('uint8');rows=[];pics={'before':[],'after':[]}
    for n,s in SOURCES.items():
        src=H/s;before=np.array(Image.open(src/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(src/f'after_{n:03}_indices.png'));after=fresh.copy();gold=[]
        if n in(170,174):
            sample=np.array(Image.open(src/f'before_{n:03}_sample_rgba.png'))
            for py,px in np.argwhere((before>0)&(y<-7)&(y>-23)&(x>=-12)&(x<=4)):
                r,g,b,alpha=map(int,sample[py-112,px-112])
                if g>=140 and r-g>=10 and g-b>=25 and before[py,px]!=7:
                    gold.append({'xy':[int(px-160),int(py-160)],'RGBA':[r,g,b,alpha],'old':int(before[py,px]),'new':7});before[py,px]=7
        bx,by=BRAID[n];head=(y<HEAD_CUT[n])|((x>=bx)&(y<by))
        if n==162:legs=((y>=5)&(x<3))|(y>=9)
        elif n==166:legs=((y>=6)&(x<3))|(y>=10)
        elif n==170:legs=((y>=10)&(x<3))|((y>=14)&(x<=8))|(y>=17)
        else:legs=y>=14
        hand=poly(HAND[n])&np.isin(before,[10,12,13]);common=head|legs|hand;after[common]=lut[before][common]
        over=np.where(same_rgba(a,before,after),0,before).astype('uint8');layers={0:after,5:over,**{b:np.zeros_like(after)for b in(6,7,8)}}
        outside=(after>0)&(before==0);actual=compose(a,layers,15);expected=a.rgba(before,16)
        delta=int(np.any(np.array(actual)!=np.array(expected),axis=2).sum())
        for form,z,mask,pal in [('before',before,15,16),('after',after,0,0)]:
            Image.fromarray(z).save(d/f'{form}_{n:03}_indices.png');compose(a,layers,mask).save(d/f'{form}_{n:03}.png');pics[form].extend([(f'{n} native',Image.open(src/f'{form}_{n:03}.png')),(f'{n} common draft',compose(a,layers,mask))])
        for k,m in [('head',head),('legs',legs),('hand',hand),('common',common),('outside_before',outside)]:Image.fromarray(m.astype('uint8')*255).save(d/f'{n:03}_{k}_mask.png')
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'source':s,'gold_source_samples':gold,'head_y_lt':HEAD_CUT[n],'braid_x_ge_y_lt':[bx,by],'hand_polygon':HAND[n],'common_opaque':int((common&(before>0)).sum()),'after_changes':int((after!=fresh).sum()),'before_composite_difference':delta,'unresolved_after_outside_before':[[int(px)-160,int(py)-160,int(after[py,px])]for py,px in zip(*np.nonzero(outside))],'components':{form:int(label(z>0,np.ones((3,3)))[1])for form,z in [('before',before),('after',after)]},'metrics':{form:metrics(a.rgba(z,pal))for form,z,pal in [('before',before,16),('after',after,0)]}})
    for form,mask in [('before',15),('after',0)]:
        for i in range(2):page(pics[form][i*4:i*4+4],a.composite(0,mask)[0],d/f'{form}_comparison_{i:02}.png',cols=2,scale=5)
    write(d/'report.json',{'parent_sha256':sha(a.data),'sources':{s:sha((H/s/'report.json').read_bytes())for s in set(SOURCES.values())},'before16_to_after0':lut.tolist(),'rows':rows,'arc_written':False,'common_and_partial_review_pending':True,'foot170_one_pixel_low_pending':True,'old_coarse_art_copied':False});print(json.dumps([{k:r[k]for k in('ref','before_composite_difference','unresolved_after_outside_before','components')}for r in rows]))
if __name__=='__main__':main()
