"""새 공중 원화의 머리/맨다리만 두 의상에서 같은 구조로 공유하는 후보."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
HEAD={33:[(-17,-25),(11,-25),(11,1),(8,6),(3,7),(0,-1),(-2,-5),(-11,-5),(-17,-8)],35:[(-17,-25),(11,-25),(11,1),(8,7),(3,7),(0,-1),(-2,-5),(-11,-5),(-17,-8)],39:[(-15,-27),(2,-27),(3,-21),(12,-20),(14,-5),(15,2),(9,6),(4,3),(0,-2),(-9,-2),(-15,-8)]}
LEGS={33:[(-11,7),(-2,7),(2,8),(5,13),(3,19),(-13,19)],35:[(-11,6),(-4,6),(-4,8),(0,9),(4,13),(2,21),(-4,21),(-5,12),(-11,10)],39:[(-12,3),(-2,3),(-1,6),(5,7),(7,17),(0,18),(-4,9),(-13,7)]}
HEAD.update({37:[(-18,-26),(13,-26),(14,1),(10,7),(5,9),(0,1),(-3,-5),(-12,-5),(-18,-10)],41:[(-14,-27),(2,-27),(3,-22),(12,-21),(14,-5),(15,2),(9,6),(4,3),(0,-2),(-10,-2),(-15,-8)],43:[(-14,-27),(12,-27),(12,-3),(14,4),(8,8),(4,3),(0,-3),(-10,-3),(-15,-9)]})
LEGS.update({37:[(-11,5),(-3,5),(-3,8),(2,10),(6,15),(4,21),(-2,21),(-5,13),(-12,9)],41:[(-12,5),(-3,5),(-2,8),(5,10),(7,20),(1,21),(-5,13),(-13,9)],43:[(-12,5),(-3,5),(-2,8),(5,10),(7,20),(1,21),(-5,13),(-13,9)]})
def polygon(points):
    q=Image.new('1',(384,384));ImageDraw.Draw(q).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(q,bool)
def main():
    out=H/'ultimate_air_common_probe02';need(not out.exists(),'Fresh source registration only');out.mkdir();a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes());need(sha(a.data)=='71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597','Wrong parent');rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics=[]
    for n in(33,35,37,39,41,43):
        folder='ultimate_air_native01'if n in(33,35,39)else'ultimate_air_native02_corrected02';before=np.array(Image.open(H/f'{folder}/before_{n:03}_indices.png'));fresh=np.array(Image.open(H/f'{folder}/after_{n:03}_indices.png'));after=fresh.copy();head=polygon(HEAD[n])
        if n not in(39,41,43):head&=(y<=-6)|np.isin(before,[0,1,2,4,5,7,8,14,15])
        else:
            face=(x>=-10)&(x<=-3)&(y>=-12)&(y<=-3)
            head&=np.isin(before,[0,1,2,4,5,7,8,14,15])|face
            head&=~((x>=1)&(x<=5)&(y>=-24)&(y<=-2))
            head&=~((x<=-10)&(y<=-18))
        legs=polygon(LEGS[n]);legs&=(y>=13)|np.isin(before,[0,1,2,10,11,12,13,15]);common=head|legs;after[common]=lut[before][common]
        edge=(after>0)&(before==0);points=[]
        for py,px in zip(*np.nonzero(edge)):
            val=int(after[py,px]);points.append([int(px)-160,int(py)-160,val]);need(val in(2,5,8,15),'Unreviewed outside material requires specific source correction');need(np.array_equal(rgb[val],rgb[16+val]),'Common edge is not RGB-exact');before[py,px]=val
        need(not np.any((after>0)&(before==0)),'After alpha outside jacket');need(np.array_equal(after[~common],fresh[~common]),'Fresh torso/bare arms altered')
        for form,v,pal in(('before',before,16),('after',after,0)):
            Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png');a.rgba(v,pal).save(out/f'{form}_{n:03}.png')
        Image.fromarray(common.astype(np.uint8)*255).save(out/f'{n:03}_common_mask.png');Image.fromarray(head.astype(np.uint8)*255).save(out/f'{n:03}_head_mask.png');Image.fromarray(legs.astype(np.uint8)*255).save(out/f'{n:03}_legs_mask.png');pics.extend([(f'{n} new jacket source',a.rgba(before,16)),(f'{n} bare arms / shared hair legs',a.rgba(after,0))]);rows.append({'ref':n,'source_head_polygon':HEAD[n],'source_legs_polygon':LEGS[n],'head_pixels':int(np.count_nonzero(before[head])),'leg_pixels':int(np.count_nonzero(before[legs])),'after_common_changed_pixels':int(np.count_nonzero(after!=fresh)),'before_added_new_after_outline_pixels':points,'outside_common_after_exact':True,'after_alpha_subset':True,'old_art_copied':0,'before_metrics':metrics(a.rgba(before,16)),'after_metrics':metrics(a.rgba(after,0))})
    [page(pics[i:i+6],a.composite(0,15)[0],out/f'comparison_{i//6:02}.png',cols=2,scale=5) for i in range(0,len(pics),6)];write(out/'report.json',{'passed':True,'source_folder':'ultimate_air_native01','palette_mapping':lut.tolist(),'rows':rows,'native_translation':[0,0],'foot_and_hand_final_registration_pending':True,'arc_written':False,'candidate_only':True});print(json.dumps([{'ref':r['ref'],'edges':r['before_added_new_after_outline_pixels'],'common_changed':r['after_common_changed_pixels']}for r in rows]))
if __name__=='__main__':main()
