"""노바 준비 두 새 몸체를 공통머리·손과 네 아머 소유로 나누는 첫 검사."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from compose_nova_fourth_costume import poly
ARM={213:[(-16,2),(-9,2),(-6,8),(-5,14),(-9,17),(-14,15)],215:[(-21,-29),(-10,-29),(-11,-21),(-10,-14),(-9,-8),(-8,-2),(-12,1),(-16,-8),(-20,-16)]}
DECO={213:[(2,-10),(15,-10),(16,3),(5,3)],215:[(0,-23),(15,-23),(15,-5),(4,-5)]}
HANDS={213:[[(-16,2),(-9,2),(-9,8),(-16,8)],[(2,10),(9,10),(9,15),(2,15)]],215:[[(-21,-29),(-10,-29),(-10,-21),(-21,-21)],[(-2,6),(7,6),(7,12),(-2,12)]]}
def main():
    d=H/'nova_layers_probe01';need(not d.exists(),'새 후보');d.mkdir();a=Archive((H/'prepared_chaser_base01/PL00_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:32]],np.int32);remap=1+np.argmin(((rgb[:16,None]-rgb[None,17:32])**2).sum(2),axis=1);rows=[]
    for n in (213,215):
        base=np.array(Image.open(H/f'nova_base_native01/base_{n:03}_indices.png'));fourth=np.array(Image.open(H/f'nova_fourth_costume_composed01/fourth_{n:03}_indices.png'))
        arm=poly(ARM[n]);deco=poly(DECO[n]);cut=8 if n==213 else -3
        braid=(x>=9)&(y>=cut)&(y<(24 if n==213 else 18));head=((y<cut)&~arm&~deco)|braid
        hands=np.logical_or.reduce([poly(ps)for ps in HANDS[n]])&np.isin(base,[10,12,13]);common=head|hands
        over=fourth.copy();over[common]=0;missing=(base>0)&(over==0)&~common
        outline=missing&np.isin(base,[2,15]);over[outline]=remap[base[outline]];pending=missing&~outline
        owner=np.full(base.shape,6,np.uint8);owner[y>=(16 if n==213 else 7)]=8;owner[(y<cut)|deco|braid]=5;owner[arm]=7
        layers={0:base,**{b:np.where(owner==b,over,0).astype('uint8')for b in(5,6,7,8)}}
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        for k,z in [('common',common),('head',head),('hands',hands),('arm',arm),('deco',deco),('outline',outline),('unresolved',pending)]:Image.fromarray(z.astype('uint8')*255).save(d/f'{n:03}_{k}_mask.png')
        Image.fromarray(owner).save(d/f'{n:03}_owner.png');partial=[]
        for m in range(16):
            im=compose(a,layers,m);labs,_=label(np.array(im)[:,:,3]>0,np.ones((3,3)));partial.append({'mask':m,'components':sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True)})
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        for form,m in [('base',0),('fourth',15)]:compose(a,layers,m).save(d/f'{form}_{n:03}.png')
        rows.append({'ref':n,'common_new_head_pixels':int((head&(base>0)).sum()),'common_hand_pixels':int(hands.sum()),'outline_registration':[[int(px)-160,int(py)-160,int(base[py,px]),int(over[py,px])]for py,px in zip(*np.nonzero(outline))],'unresolved':[[int(px)-160,int(py)-160,int(base[py,px])]for py,px in zip(*np.nonzero(pending))],'partial':partial,'layers':{str(b):sha(z.tobytes())for b,z in layers.items()}})
    for form,m in [('base',0),('fourth',15)]:page([(f'{n} 既存',a.composite(n,m)[0])if i==0 else(f'{n} 새 공통부',Image.open(d/f'{form}_{n:03}.png'))for n in(213,215)for i in(0,1)],a.composite(0,m)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'rows':rows,'unresolved_cells':sum(len(r['unresolved'])for r in rows),'policy':'새 기본형의 머리·손 공통부와 새 포스 의상 의미영역. 아직 외곽 미정합·부분조합 검토 후보이며 ARC 미작성.','arc_written':False,'body_resized':False});print(json.dumps([{'ref':r['ref'],'unresolved':r['unresolved'],'outline':len(r['outline_registration']),'partial_components':[len(p['components'])for p in r['partial']]}for r in rows]))
if __name__=='__main__':main()
