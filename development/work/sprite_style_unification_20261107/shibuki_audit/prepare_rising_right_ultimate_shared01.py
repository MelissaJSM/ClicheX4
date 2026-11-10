"""오른손 발사 자세103/104의 새 전후 원화만 공통 부위 등록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
from prepare_lowhp_final import polygon
from prepare_rising_right_base_layers01 import HEADS,FACE,DECOS
def main():
    out=H/'rising_right_ultimate_shared02';need(not out.exists(),'Fresh output');out.mkdir();a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+(((rgb[17:32,None]-rgb[None,1:16])**2).sum(2)).argmin(1)].astype(np.uint8)
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics=[]
    for n in(103,104):
        d=H/('rising_ultimate_prepare103_native01'if n==103 else'rising_ultimate_right_native02')
        before=np.array(Image.open(d/f'before_{n}_indices.png'));fresh=np.array(Image.open(d/f'after_{n}_indices.png'))
        # Original current103 bottom sole y24; new art bottom y23. Translate
        # the entire new pose by one pixel, with no stretching or segmented edit.
        if n==103:before=np.roll(before,1,axis=0);fresh=np.roll(fresh,1,axis=0)
        after=fresh.copy();fx0,fy0,fx1,fy1=FACE[n];face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1)
        head=(polygon(HEADS[n])|polygon(DECOS[n]))&(np.isin(before,[0,1,2,4,5,7,8,14,15])|face)
        # Newly generated matching hair/skin/ornament pixels are shared. This
        # mask excludes both new white sleeves and the bare-arm source regions.
        if n==103:head&=~((x>=1)&(x<=7)&(y>=-3)&(y<=7))
        else:head&=~((x>=2)&(y<=-18))
        legs=y>=11
        if n==103:palms=((x>=1)&(x<=6)&(y>=-3)&(y<=2))|((x>=-14)&(x<=-8)&(y>=1)&(y<=5))
        else:palms=((x>=1)&(x<=7)&(y<=-25))|((x>=-16)&(x<=-10)&(y>=-5)&(y<=0))
        palms&=np.isin(before,[10,11,12,13])
        common=head|legs|palms;after[common]=lut[before][common]
        uncovered=(after>0)&(before==0);points=[[int(px)-160,int(py)-160,int(after[py,px])]for py,px in zip(*np.nonzero(uncovered))]
        need(points==([]if n==103 else[[-14,-2,15]]),'Unreviewed source contour')
        contour=points.copy()
        for px,py,val in contour:
            need(np.array_equal(rgb[val],rgb[16+val]),'Source outline palette differs')
            before[py+160,px+160]=val
        points=[]
        for form,v,pal in(('before',before,16),('after',after,0)):
            Image.fromarray(v).save(out/f'{form}_{n}_indices.png');a.rgba(v,pal).save(out/f'{form}_{n}.png')
        Image.fromarray(common.astype(np.uint8)*255).save(out/f'{n}_common_mask.png')
        pics.extend([(f'{n} new jacket / registered',a.rgba(before,16)),(f'{n} new bare arms + shared hair/legs',a.rgba(after))])
        rows.append({'ref':n,'translation':[0,1 if n==103 else 0],'after_outside_common_exact':bool(np.array_equal(after[~common],fresh[~common])),'uncovered':points,'before_added_exact_new_after_contour':contour,'after_changed_from_fresh':int(np.count_nonzero(after!=fresh)),'new_common_pixels':int(np.count_nonzero(before[common])),'before':metrics(a.rgba(before,16)),'after':metrics(a.rgba(after)),'old_art_pixels':0})
    page(pics,a.composite(0,15)[0],out/'comparison.png',cols=2,scale=5);write(out/'report.json',{'candidate_only':True,'rows':rows,'palette_lut':lut.tolist(),'passed_alpha_subset':all(not r['uncovered']for r in rows),'resource_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
