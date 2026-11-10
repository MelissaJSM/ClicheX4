"""새 보행 사격팔을 원화 의미영역에서 등록한다. 전체 원화 덮기 금지."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from probe_dash_common_head import poly
from prepare_dash_body_layers import rect
REMOVED={
0:[(-17,-3),(-12,-3),(-11,-1),(-8,-2),(-5,1),(-6,6),(-9,8),(-10,15),(-15,15),(-16,10),(-17,6)],
3:[(-12,-5),(-8,-5),(-8,-3),(-5,-2),(-4,1),(-5,5),(-8,7),(-8,11),(-11,11),(-11,7),(-13,7),(-14,4),(-14,0)],
5:[(-17,-4),(-13,-4),(-13,-1),(-11,-2),(-9,-1),(-6,1),(-5,5),(-7,8),(-10,8),(-11,10),(-14,10),(-15,6),(-17,1)],
7:[(-17,-1),(-13,-1),(-13,1),(-10,0),(-7,1),(-5,4),(-6,7),(-8,10),(-13,10),(-15,8),(-17,4)],
9:[(-15,-2),(-10,-2),(-9,-4),(-6,-3),(-5,3),(-5,7),(-7,10),(-11,9),(-12,6),(-15,4)],
11:[(-18,-5),(-14,-5),(-13,-2),(-10,-3),(-9,0),(-9,6),(-11,7),(-12,10),(-15,10),(-15,6),(-18,1)],
13:[(-15,-4),(-11,-4),(-10,-2),(-7,-3),(-6,0),(-6,4),(-9,5),(-11,4),(-13,2),(-15,1)],
15:[(-16,-4),(-11,-4),(-10,-2),(-7,-3),(-6,1),(-7,5),(-10,5),(-13,4),(-15,1)],
17:[(-16,-2),(-12,-3),(-10,0),(-7,-1),(-6,3),(-7,7),(-11,8),(-14,6),(-16,2)],
19:[(-13,-5),(-8,-5),(-7,-3),(-4,-3),(-2,0),(-3,5),(-6,7),(-7,11),(-11,11),(-12,7)],
21:[(-13,-2),(-8,-2),(-7,0),(-4,-1),(-1,1),(-1,6),(-4,8),(-8,9),(-11,9),(-11,6),(-13,4)],
23:[(-14,-4),(-9,-4),(-8,-1),(-5,-2),(-3,2),(-4,7),(-7,11),(-10,11),(-12,8),(-14,2)],
25:[(-13,-2),(-8,-2),(-8,0),(-5,-1),(-2,2),(-2,7),(-6,9),(-8,12),(-11,12),(-12,8)],
27:[(-11,-2),(-7,-2),(-6,0),(-4,1),(-4,4),(-7,5),(-10,3)],
29:[(-16,-5),(-11,-5),(-10,-3),(-7,-3),(-5,0),(-5,5),(-8,8),(-11,7),(-14,5),(-16,0)],
31:[(-16,-7),(-12,-7),(-12,-3),(-9,-4),(-5,-2),(-5,3),(-8,6),(-11,6),(-14,6),(-14,4),(-16,0)]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,default=1);ap.add_argument('--output',default='base_run_shot_page01_registered01');z=ap.parse_args();out=(H/z.output).resolve();need(out.is_relative_to(H.resolve())and not out.exists(),'Fresh isolated output');d=H/f'base_run_shot_inputs01/page{z.page:02}';q=H/f'base_run_shot_page{z.page:02}_source01';meta=json.loads((d/'manifest.json').read_text('utf8'));p=H/'prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)==meta['source_parent_sha256'],'Parent changed');full=np.array(Image.open(d/'generated.png'));rows=[];basepairs={};yy,xx=np.indices((384,384));xx-=160;yy-=160;out.mkdir()
    for form,mask,pal in(('base',0,0),('fourth',15,16)):
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for r in [r for r in meta['rows']if r['form']==form]:
            n=r['shot_ref'];bn=r['body_ref'];ex,ey=r['eye'];sx,sy=r['shoulder'];mx,my=r['barrel']['muzzle_world'];col,row=r['cell'];source=np.array(Image.open(q/f'{form}_{n:03}_source_indices.png'));gun=np.array(Image.open(H/f'base_run_shot_inputs01/barrels/{n:03}_indices.png'));guard=np.array(Image.open(H/f'base_run_shot_inputs01/barrels/{n:03}_mask.png'))>0
            if bn==0:before=np.array(a.composite(0,mask)[0]);baseidx=a.layer(0,0)[0];common=yy<=-5
            else:before=np.array(Image.open(H/f'base_run_common01/{form}_{bn:03}.png').convert('RGBA'));baseidx=np.array(Image.open(H/f'base_run_common01/{bn:03}_base_indices.png'));common=np.array(Image.open(H/f'base_run_common01/{bn:03}_common_mask.png'))>0
            added=poly([(mx+8,my-4),(sx-5,my-3),(sx+3,sy-3),(sx+3,sy+4),(sx-6,sy+5),(mx+8,my+6)]);face=rect((ex-4,ey-3,ex+5,ey+4));protected_head=common&(baseidx>0)&(yy<=ey+4);patch=(poly(REMOVED[bn])|added)&~face&~protected_head&~guard
            if bn==0:
                # Native leg8 also owns the old dangling sleeve (tile10 first
                # four rows). Technical layer ownership is not anatomy.
                # Preserve the actual knee/leg: x>=-9, and x=-10 below y11.
                # The independent layer audit identifies x<=-11/y11..14 as
                # the old cuff; here the new source is transparent.
                knee=((xx>=-9)|((xx>=-10)&(yy>=12)))&(yy>=8)
                patch&=~knee
            target=before.copy();target[patch]=np.array(a.rgba(source,pal))[patch];target[guard]=np.array(a.rgba(gun))[guard];allowed=patch|guard;edge=[]
            if form=='fourth':
                base=basepairs[n];outside=(base[:,:,3]>0)&(target[:,:,3]==0);need(np.all(allowed[outside]),'Body outside common alpha')
                for py,px in zip(*np.nonzero(outside)):
                    block=full[row*512+(py-124)*8:row*512+(py-123)*8,col*512+(px-128)*8:col*512+(px-127)*8];valid=block[:,:,3]>=128;count=int(valid.sum());idx=0
                    if count>=8:
                        qq=1+((block[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2);v,c=np.unique(qq[valid],return_counts=True);idx=int(v[c.argmax()]);source[py,px]=idx;target[py,px]=np.array(a.rgba(np.array([[idx]],np.uint8),pal))[0,0]
                    method='fourth_source_cell'if count>=8 else 'unresolved'
                    outline_cells={2:((-16,-10),(-11,-7),(-18,-5),(-17,-4),(-14,-2)),14:((-11,1),(-12,2)),20:((-15,-9),),24:((-8,5),)}
                    if (int(px)-160,int(py)-160)in outline_cells.get(n,()) and count<8:
                        # The newly drawn basic garment has two dark contour
                        # texels outside the Fourth source. Preserve that new
                        # contour in Fourth's matching dark-purple outline;
                        # this never invents a skin/fabric interior or copies
                        # the old accepted sprite. Explicit two-cell scope.
                        base_source=np.array(Image.open(q/f'base_{n:03}_source_indices.png'));bindex=int(base_source[py,px]);expected=2 if n==2 and(int(px)-160,int(py)-160)==(-11,-7)else 15;need(bindex==expected,'Expected new dark contour changed');need(not np.all(base[py-1:py+2,px-1:px+2,3]>0),'Contour became an interior');idx=2 if bindex==2 else 1;source[py,px]=idx;target[py,px]=np.array(a.rgba(np.array([[idx]],np.uint8),pal))[0,0];method=f'new_base_outline{bindex}_to_fourth_outline{idx}'
                    edge.append({'world':[int(px)-160,int(py)-160],'source_opaque_samples':count,'index':idx,'source_supported':count>=8,'method':method,'resolved':idx!=0})
            else:basepairs[n]=target.copy()
            need(np.array_equal(target[~allowed],before[~allowed]),'Non-arm body changed');need(np.array_equal(target[face&~guard],before[face&~guard]),'Face changed');need(np.array_equal(target[protected_head&~guard],before[protected_head&~guard]),'Registered head changed');need(np.array_equal(target[guard],np.array(a.rgba(gun))[guard]),'Gun changed')
            if form=='base':
                indices=baseidx.copy();indices[patch]=source[patch];indices[guard]=gun[guard];Image.fromarray(indices).save(out/f'{form}_{n:03}_indices.png')
            for name,m in(('allowed',allowed),('patch',patch),('protected_head',protected_head)):Image.fromarray(m.astype(np.uint8)*255).save(out/f'{form}_{n:03}_{name}_mask.png')
            Image.fromarray(source).save(out/f'{form}_{n:03}_registered_arm_indices.png');Image.fromarray(target).save(out/f'{form}_{n:03}.png');lab,nc=label(target[:,:,3]>0,np.ones((3,3),int));sizes=sorted([int((lab==i).sum())for i in range(1,nc+1)],reverse=True);contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(target[:,:,3]>0)&~guard
            rows.append({'form':form,'ref':n,'body_ref':bn,'source_sha256':sha((d/'generated.png').read_bytes()),'changed_pixels':int(np.any(target!=before,axis=2).sum()),'components8':sizes,'arm_boundary_source_samples':edge,'uncovered_base_cells':[e['world']for e in edge if not e['resolved']],'barrel_adjacent_pixels':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(contact))],'outside_arm_exact':True,'head_exact':True,'muzzle_rgba_exact':True});pics.extend([(f'{bn} new body',Image.fromarray(before)),(f'{n} source arm / fixed gun',Image.fromarray(target))])
        page(pics,a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=6)
    write(out/'report.json',{'candidate_only':True,'rows':rows,'source_report_sha256':sha((q/'report.json').read_bytes()),'parent_sha256':sha(a.data),'arm_source_only':True,'alpha_registration_passed':not any(r['uncovered_base_cells']for r in rows),'arc_written':False,'visual_review_pending':True,'runtime_verified':False});print(json.dumps({'displays':len(rows),'components':[r['components8']for r in rows],'uncovered':[r['uncovered_base_cells']for r in rows]}))
if __name__=='__main__':main()
