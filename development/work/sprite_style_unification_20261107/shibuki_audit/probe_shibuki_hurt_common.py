"""새 피격4의 공통 머리·장식과 의상 경계 시험. ARC 미작성."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import polygon,compose

REGION={
106:[(-24,-28),(24,-28),(24,12),(10,13),(9,6),(5,3),(5,-2),(-5,-2),(-11,-2),(-24,-3)],
110:[(-24,-28),(24,-28),(24,17),(7,17),(7,8),(4,6),(3,0),(-1,-1),(-6,-2),(-13,-1),(-14,-3),(-24,-4)],
233:[(-20,-28),(20,-28),(20,7),(8,7),(4,1),(2,-3),(-1,-3),(-5,-3),(-12,-3),(-20,-4)],
234:[(-24,-28),(24,-28),(24,16),(3,17),(4,11),(7,9),(7,5),(4,2),(2,-1),(-2,-3),(-6,-3),(-8,-5),(-12,-4),(-24,-4)]}
FACE={106:(-13,-10,2,-1),110:(-12,-8,2,-1),233:(-13,-11,1,-2),234:(-14,-8,1,-2)}
DEC={106:(6,-13,16,2),110:(7,-5,17,8),233:(5,-15,16,1),234:(-5,-21,11,-5)}
ARM={106:[(-14,0),(-9,-1),(-8,4),(-10,8),(-13,11),(-19,11),(-19,4)],110:[(-13,-4),(-8,-3),(-6,1),(-6,4),(-12,5),(-17,3),(-17,0)],233:[(-25,-8),(-16,-9),(-11,-4),(-10,1),(-15,4),(-25,3)],234:[(-20,-6),(-11,-6),(-7,-4),(-2,-3),(-3,2),(-7,6),(-13,5),(-18,2)]}
LEG={106:[(-13,10),(-8,10),(-3,11),(1,10),(2,12),(8,15),(8,26),(-18,26)],110:[(-18,7),(-10,8),(-6,10),(-4,11),(0,13),(2,22),(-10,22),(-17,15)],233:[(-24,0),(-18,0),(-14,4),(-12,9),(-8,10),(-5,10),(0,17),(0,26),(-12,26),(-18,18),(-23,11)],234:[(-14,9),(-8,9),(-4,10),(2,11),(2,17),(-8,26),(-19,26),(-19,19)]}

def rect(t):
    x1,y1,x2,y2=t;y,x=np.indices((384,384));return(x>=160+x1)&(x<160+x2)&(y>=160+y1)&(y<160+y2)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='hurt_common_probe01');z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh output');o.mkdir()
    a=Archive((H/'prepared_base_run01/PL00_U.ARC').read_bytes());need(sha(a.data)=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce','Parent changed');rows=[];pics=[]
    rgb=np.array([[(int(w)>>ss&31)*255//31 for ss in(0,5,10)]for w in a.words[16:32]],np.int32)
    for n in (106,110,233,234):
        pageid=1 if n<200 else 2;col=(106,110).index(n)if pageid==1 else(233,234).index(n);d=H/f'hurt_native{pageid:02}';base=np.array(Image.open(d/f'base_{n:03}_indices.png'));raw=np.array(Image.open(d/f'fourth_{n:03}_indices.png'));src=np.array(Image.open(H/f'hurt_inputs01/page{pageid:02}/generated.png').convert('RGBA'))
        region=polygon(REGION[n]);face=rect(FACE[n]);dec=rect(DEC[n]);common=region&(np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13])));common|=dec
        over=raw.copy();over[common]=0;over[dec]=raw[dec];edge=(base>0)&(over==0)&(~common|dec);fix=[];unresolved=[]
        for py,px in zip(*np.nonzero(edge)):
            wx,wy=int(px)-160,int(py)-160;cell=src[512+(wy+32)*8:512+(wy+33)*8,col*768+(wx+48)*8:col*768+(wx+49)*8];m=cell[:,:,3]>=128;coverage=int(m.sum());r={'world':[wx,wy],'base_index':int(base[py,px]),'source_opaque':coverage}
            if coverage>=8 or (n,wx,wy,coverage) in ((106,11,-4,7),(233,9,-4,4)):
                q=1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2);v,c=np.unique(q[m],return_counts=True);idx=int(v[c.argmax()]);over[py,px]=idx;r.update(fourth_index=idx,method='new_generated_8x8_opaque_mode',histogram=dict(zip(map(str,v),map(int,c))));fix.append(r)
            elif n==233 and (wx,wy) in ((9,-5),(10,-5),(10,-4)):
                # The newly painted base ribbon is wider by two contour columns.
                # Preserve its alpha and reuse the NEW Fourth ornament's nearby
                # gold-shadow/outline texels; never delete/flatten the body.
                source=(7,-5)if(wx,wy)==(9,-5)else(9,-3);idx=int(raw[source[1]+160,source[0]+160]);need(idx==(11 if source==(7,-5)else 1),'Source ornament changed');over[py,px]=idx
                r.update(fourth_index=idx,method='new_ornament_contour_registration',donor_world=list(source),donor_index=idx,not_exact_generated_alpha=True);fix.append(r)
            else:unresolved.append(r)
        owner=np.full(base.shape,6,np.uint8);owner[polygon(LEG[n])]=8;owner[polygon(ARM[n])]=7;owner[dec]=5
        layers={0:base};layers.update({b:np.where(owner==b,over,0).astype(np.uint8)for b in(5,6,7,8)})
        full=compose(a,layers,15);full.save(o/f'fourth_{n:03}.png');a.rgba(base).save(o/f'base_{n:03}.png')
        for b,v in layers.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
        for name,v in(('common_mask',common.astype(np.uint8)*255),('decoration_mask',dec.astype(np.uint8)*255),('owner',owner),('unresolved_mask',(edge&(over==0)).astype(np.uint8)*255)):Image.fromarray(v).save(o/f'{n:03}_{name}.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=3)
        pics.extend([(f'{n} raw new Fourth',a.rgba(raw,16)),(f'{n} common new head / boundary probe',full)])
        rows.append({'ref':n,'page':pageid,'new_source_sha256':sha((H/f'hurt_inputs01/page{pageid:02}/generated.png').read_bytes()),'new_common_head_opaque':int((common&(base>0)).sum()),'decoration_rect':DEC[n],'arm_polygon':ARM[n],'leg_polygon':LEG[n],'boundary_registered':fix,'boundary_unresolved':unresolved,'layer_pixels':{str(b):int((v>0).sum())for b,v in layers.items()},'old_head_or_body_copied':False,'wholebody_resized':False,'new_base_pixels_exact':True})
    for k in range(0,len(pics),4):page(pics[k:k+4],a.composite(0,15)[0],o/f'comparison_{k//4:02}.png',cols=2,scale=5)
    write(o/'report.json',{'candidate_only':True,'parent_sha256':sha(a.data),'rows':rows,'policy':'새 기본 머리/얼굴은 공통이고 새 포스 장식만 Head, 앞팔 Arm, 상의/뒷팔 Body, 하체 Leg로 분리. 투명 때문에 남는 기본 의상은 새 원화의 실제8x8 표본을 읽고 부족하면 미해결로 남긴다.','partial_visual_review_pending':True,'arc_written':False,'effects_pending':True,'runtime_verified':False});print(json.dumps([{'ref':r['ref'],'registered':len(r['boundary_registered']),'unresolved':r['boundary_unresolved'],'layers':r['layer_pixels']}for r in rows]))
if __name__=='__main__':main()
