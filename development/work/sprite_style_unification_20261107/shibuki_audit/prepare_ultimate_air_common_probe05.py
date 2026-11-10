"""후반5공중 자세의 새 머리/다리 공통층 등록 진단. 미해결 팔은 숨기지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
from prepare_lowhp_final import polygon
HEAD={45:[(-17,-26),(13,-26),(13,-5),(11,5),(7,8),(3,5),(1,-4),(-8,-4),(-15,-5)],47:[(-18,-26),(13,-26),(13,-4),(12,5),(7,9),(3,5),(0,-3),(-9,-3),(-16,-6)],49:[(-18,-26),(13,-26),(14,0),(14,9),(8,12),(3,8),(0,-2),(-10,-2),(-17,-5)],51:[(-18,-23),(14,-23),(14,1),(13,10),(8,12),(3,8),(0,-1),(-10,-1),(-17,-5)],53:[(-20,-24),(14,-24),(14,1),(14,10),(8,13),(3,8),(0,-1),(-10,-1),(-18,-5)]}
LEGS={45:[(-12,6),(-3,6),(1,9),(6,15),(4,23),(-2,23),(-7,14),(-12,10)],47:[(-13,6),(-3,6),(1,9),(6,15),(4,23),(-2,23),(-7,14),(-13,10)],49:[(-14,7),(8,7),(14,25),(-16,25)],51:[(-13,8),(8,8),(14,25),(-15,25)],53:[(-14,8),(8,8),(14,25),(-16,25)]}
def main():
    out=H/'ultimate_air_common_probe05'
    if out.exists()and not any(out.iterdir()):out.rmdir()
    need(not out.exists(),'Fresh output');out.mkdir();a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics=[]
    for n in(45,47,49,51,53):
        d=H/('ultimate_air_native03'if n<51 else'ultimate_air_native04');before=np.array(Image.open(d/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(d/f'after_{n:03}_indices.png'));after=fresh.copy()
        head=polygon(HEAD[n]);face=(x>=-11)&(x<=-2)&(y>=-14)&(y<=-4)
        head&=(y<=-8)|np.isin(before,[0,1,2,4,5,7,8,14,15])|face
        # Both real arms are excluded, even where white cuffs touch rear hair.
        head&=~(((x<=-10)&(y>=-9))|((x>=3)&(x<=9)&(y>=-7)&(y<=4)))
        head&=~((x>=(-2 if n==47 else 0))&(x<=10)&(y>=(-5 if n==45 else -4))&(y<=10))
        legs=polygon(LEGS[n]);legs&=(y>=13)|np.isin(before,[0,1,2,10,11,12,13,15]);common=head|legs;after[common]=lut[before][common]
        edge=(after>0)&(before==0);points=[];allowed=[];unresolved=[]
        for py,px in zip(*np.nonzero(edge)):
            val=int(after[py,px]);row=[int(px)-160,int(py)-160,val];points.append(row)
            if val in(2,5,8,15)and np.array_equal(rgb[val],rgb[16+val]):before[py,px]=val;allowed.append(row)
            else:unresolved.append(row)
        for form,v,pal in(('before',before,16),('after',after,0)):
            Image.fromarray(v).save(out/f'{form}_{n}_indices.png');a.rgba(v,pal).save(out/f'{form}_{n}.png')
        Image.fromarray(common.astype(np.uint8)*255).save(out/f'{n}_common_mask.png');Image.fromarray(head.astype(np.uint8)*255).save(out/f'{n}_head_mask.png');Image.fromarray(legs.astype(np.uint8)*255).save(out/f'{n}_legs_mask.png')
        pics.extend([(f'{n} jacket / new common head',a.rgba(before,16)),(f'{n} swimsuit / bare source arms',a.rgba(after))]);rows.append({'ref':n,'source_folder':str(d.relative_to(H)),'common_head_polygon':HEAD[n],'common_leg_polygon':LEGS[n],'new_head_pixels':int(np.count_nonzero(before[head])),'new_leg_pixels':int(np.count_nonzero(before[legs])),'source_outline_union':allowed,'unresolved_new_after_outside_jacket':unresolved,'after_outside_common_exact':bool(np.array_equal(after[~common],fresh[~common])),'after_changed_pixels':int(np.count_nonzero(after!=fresh)),'before':metrics(a.rgba(before,16)),'after':metrics(a.rgba(after)),'old_art_copied':0})
    for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,15)[0],out/f'comparison_{i//6:02}.png',cols=2,scale=5)
    write(out/'report.json',{'candidate_only':True,'rows':rows,'passed_subset':all(not r['unresolved_new_after_outside_jacket']for r in rows),'palette_lut':lut.tolist(),'resource_written':False,'joint_contact_and_arms_pending':True});print(json.dumps([{'ref':r['ref'],'outline':len(r['source_outline_union']),'unresolved':r['unresolved_new_after_outside_jacket']}for r in rows]))
if __name__=='__main__':main()
