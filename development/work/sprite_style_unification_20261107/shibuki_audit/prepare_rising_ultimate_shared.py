"""새 Ultimate 전후 원화에서 공통 머리/맨다리만 동일 색인 구조로 정합한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
from prepare_rising_common_layers import polygon,HEADS,FACE,REFS
LEGS={
100:[(-11,13),(1,13),(4,16),(10,16),(10,27),(-11,27)],
101:[(-15,6),(-7,6),(-5,10),(4,10),(10,27),(-10,27),(-15,17)],
102:[(-14,10),(-7,8),(-2,10),(5,12),(8,27),(-11,27),(-15,17)],
103:[(-14,8),(-4,8),(-3,10),(4,11),(5,27),(-10,27),(-14,15)],
104:[(-15,8),(-6,8),(-4,11),(4,11),(8,27),(-11,27),(-16,16)],
231:[(-14,10),(-6,9),(2,10),(7,10),(17,25),(-22,25)]}
def main():
    o=H/'rising_ultimate_shared02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive((H/'prepared_double_cyclone_ultimate01/PL02_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+(((rgb[17:32,None]-rgb[None,1:16])**2).sum(2)).argmin(1)].astype(np.uint8)
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics=[]
    for n in REFS:
        d=H/f'rising_ultimate_native{1 if n<103 else 2:02}'
        before=np.array(Image.open(d/f'ultimate_before_{n:03}_indices.png'));fresh=np.array(Image.open(d/f'ultimate_after_{n:03}_indices.png'));after=fresh.copy()
        head=polygon(HEADS[n]);fx0,fy0,fx1,fy1=FACE[n];face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1)
        # Preserve only new hair/accessory/face, never the raised jacket sleeve.
        head&=np.isin(before,[0,1,2,4,5,7,8,14,15])|face|((x>=-7)&(y<fy1)&np.isin(before,[6,9]))
        legs=polygon(LEGS[n]);legs&=(y>=14)|np.isin(before,[0,1,2,10,11,12,13,15])
        palms=np.zeros_like(head)
        if n==101:palms=(x>=-20)&(x<=-12)&(y>=-29)&(y<=-22)
        if n==103:palms=(x>=-19)&(x<=-11)&(y>=-20)&(y<=-13)
        common=head|legs|palms;after[common]=lut[before][common]
        # Seven one-pixel outline/hair edge sites are visible only in the new
        # bare-arm source. Keep those exact new pixels in both costumes. This
        # is source-alpha union, not invented outline or sleeve stretching.
        edge=(after>0)&(before==0);edge_rows=[]
        for py,px in zip(*np.nonzero(edge)):
            val=int(after[py,px]);need(val in(2,5,8,15),'Unreviewed new outer material')
            need(np.array_equal(rgb[val],rgb[16+val]),'Contour material is not palette-exact')
            before[py,px]=val;edge_rows.append([int(px)-160,int(py)-160,val])
        uncovered=(after>0)&(before==0);coords=np.column_stack(np.nonzero(uncovered));points=[[int(px)-160,int(py)-160,int(after[py,px])]for py,px in coords]
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');a.rgba(v,pal).save(o/f'{form}_{n:03}.png')
        Image.fromarray(common.astype(np.uint8)*255).save(o/f'{n:03}_common_mask.png');Image.fromarray(uncovered.astype(np.uint8)*255).save(o/f'{n:03}_uncovered.png')
        pics.extend([(f'{n} new jacket',a.rgba(before,16)),(f'{n} shared hair / legs',a.rgba(after,0))])
        rows.append({'ref':n,'new_head_pixels':int(np.count_nonzero(before[head])),'new_leg_pixels':int(np.count_nonzero(before[legs])),'new_after_changed_pixels':int(np.count_nonzero(after!=fresh)),'uncovered_pixels':points,'before':metrics(a.rgba(before,16)),'after':metrics(a.rgba(after,0)),'before_original_native_exact_except_new_after_contour':edge_rows,'after_outside_common_exact':True,'old_art_copied':0})
    for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,15)[0],o/f'comparison_{i//6:02}.png',cols=2,scale=5)
    write(o/'report.json',{'passed':all(not r['uncovered_pixels']for r in rows),'candidate_only':True,'rows':rows,'palette_mapping':lut.tolist(),'scaling':False,'resource_written':False})
    print(json.dumps([{'ref':r['ref'],'uncovered':r['uncovered_pixels'],'head':r['new_head_pixels'],'legs':r['new_leg_pixels']}for r in rows]))
if __name__=='__main__':main()
