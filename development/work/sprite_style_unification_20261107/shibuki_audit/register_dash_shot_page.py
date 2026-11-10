"""새 대시 사격 팔을 생성 원화의 의미 영역에서만 읽어 고정 총열에 등록."""
from pathlib import Path
import json,sys,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from prepare_dash_body_layers import rect,P,LEG
from prepare_dash_shot_inputs import GROUPS,SHOULDER
from probe_dash_common_head import poly
REMOVED={
67:[(-17,-2),(-7,-2),(-3,4),(-5,10),(-12,12),(-17,7)],
69:[(-20,3),(-9,3),(-6,8),(-8,16),(-16,18),(-21,12)],
71:[(-26,7),(-13,7),(-10,12),(-14,22),(-22,22),(-26,17)],
75:[(-25,8),(-12,8),(-9,13),(-12,23),(-21,23),(-25,18)],
77:[(-24,7),(-19,0),(-8,1),(-4,7),(-7,10),(-12,11),(-15,15),(-24,15)],
79:[(-16,0),(-4,0),(0,6),(-3,15),(-11,16),(-17,10)],
81:[(-17,0),(-4,0),(-1,6),(-3,15),(-12,16),(-18,10)],
83:[(-17,-3),(-5,-3),(-1,2),(-4,12),(-12,13),(-18,7)]}
FACE={67:(-12,-10,0,-1),69:(-15,-5,-3,4),71:(-22,1,-10,10),75:(-21,1,-9,10),77:(-16,-8,-4,1),79:(-12,-11,0,-2),81:(-13,-13,-1,-4),83:(-13,-14,-1,-5)}
def palette(a,pal):return np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',type=int,required=True,choices=range(1,5));ap.add_argument('--sha',required=True);ap.add_argument('--output',required=True);ap.add_argument('--only',type=int);ap.add_argument('--source-folder');z=ap.parse_args()
    d=(H/z.source_folder).resolve()if z.source_folder else H/f'dash_shot_inputs02/page{z.page:02}';need(d.is_relative_to(H.resolve()),'Source outside work folder');o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh isolated output required');src=d/'generated.png';need(sha(src.read_bytes())==z.sha,'Wrong source');a=Archive(P.read_bytes());im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Source dimensions');full=np.array(im);sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));gmdata=json.loads((H/'dash_barrel_guard02/report.json').read_text('utf8'));rows=[];o.mkdir();pairs={};palm_rows={}
    for row,(form,pal,mask)in enumerate((('base',0,0),('fourth',16,15))):
        colors=palette(a,pal);pics=[]
        for col,n in enumerate(GROUPS[z.page-1]):
            if z.only is not None and n+1!=z.only:continue
            cell=sample[row*64:(row+1)*64,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
            source=np.zeros((384,384),np.uint8);source[124:188,112:208]=q;Image.fromarray(source).save(o/f'{form}_{n+1:03}_source_indices.png')
            body={b:np.array(Image.open(H/f'dash_body_layers01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};before=np.array(compose(a,body,mask));gm=next(r for r in gmdata['rows']if r['body_ref']==n and r['form']==form);mx,my=gm['muzzle_world'];sx,sy=SHOULDER[n]
            added=[(mx+7,my-3),(sx-6,my-3),(sx+3,sy-3),(sx+3,sy+5),(sx-6,sy+8),(mx+7,my+7)];face=rect(FACE[n]);yy,xx=np.indices(source.shape);patch=(poly(REMOVED[n])|(poly(added)&(xx>=160+mx+8)))&~face&~poly(LEG[n])
            if n==77:patch&=~rect((-12,11,24,32)) # Preserve new knee edge beside lowered former sleeve.
            if n==81:
                patch|=rect((-15,-3,-5,5)) # New compact palm sits beneath, not behind, the near-face gun.
                patch&=~rect((-6,6,24,32)) # Foreground arm stops before the new waist/hem.
            gun=np.array(Image.open(H/f'dash_barrel_guard02/{n+1:03}_indices.png'));guard=np.array(Image.open(H/f'dash_barrel_guard02/{n+1:03}_mask.png'))>0
            target=before.copy();target[patch]=np.array(a.rgba(source,pal))[patch];target[guard]=np.array(a.rgba(gun))[guard]
            band=(xx>=160+mx+8)&(xx<160+mx+12)&(yy>=160+my-4)&(yy<160+my+5);skin=band&np.isin(source,[12,13]if form=='base'else[9]);syv,_=np.nonzero(skin);need(len(syv)>0,'No generated palm under barrel')
            if form=='base':palm_rows[n]=int(syv.min())
            ring=band&(yy<palm_rows[n])&~guard;protected_head=ring&(before[:,:,3]>0)
            common=np.array(Image.open(H/f'dash_common_head_probe01/{n:03}_common_mask.png'))>0
            need(n==81 or np.all(common[protected_head]),'Barrel area overlaps a non-head body part')
            # A close muzzle can sit beside the new front hair. Retain those
            # already registered head texels; clean only originally empty ring.
            target[protected_head]=before[protected_head];patch&=~protected_head;ring&=~protected_head;target[ring]=0;allowed=patch|guard|ring
            edge=[]
            if form=='fourth':
                base=pairs[n];outside=(base[:,:,3]>0)&(target[:,:,3]==0);need(np.all(allowed[outside]),'Unexpected body outside Fourth')
                Image.fromarray(target).save(o/f'{form}_{n+1:03}_before_alpha_coverage.png')
                write(o/f'{form}_{n+1:03}_alpha_coverage_probe.json',{'outside_pixels':[[int(x)-160,int(y)-160,int((full[(y-124)*8+row*512:(y-124)*8+row*512+8,(x-112)*8+col*768:(x-112)*8+col*768+8,3]>=128).sum())]for y,x in zip(*np.nonzero(outside))]})
                for y,x in zip(*np.nonzero(outside)):
                    px=(x-112)*8+col*768;py=(y-124)*8+row*512;block=full[py:py+8,px:px+8];valid=block[:,:,3]>=128;need(valid.sum()>=24,'Contour needs new artwork, not invented fill');rgb=np.median(block[:,:,:3][valid],axis=0);index=int(1+((colors[1:]-rgb)**2).sum(1).argmin());target[y,x]=np.array(a.rgba(np.array([[index]],np.uint8),pal))[0,0];source[y,x]=index;edge.append({'world':[int(x)-160,int(y)-160],'source_opaque_samples':int(valid.sum()),'palette_index':index})
                need(not np.any((base[:,:,3]>0)&(target[:,:,3]==0)),'Fourth alpha does not cover base')
            else:pairs[n]=target.copy()
            need(np.array_equal(target[~allowed],before[~allowed]),'Changed non-arm body');need(np.array_equal(target[face&~guard],before[face&~guard]),'Face changed');need(np.array_equal(target[guard],np.array(a.rgba(gun))[guard]),'Casing changed')
            if form=='base':
                indices=body[0].copy();indices[patch]=source[patch];indices[guard]=gun[guard];indices[ring]=0;Image.fromarray(indices).save(o/f'base_{n+1:03}_indices.png')
            Image.fromarray(source).save(o/f'{form}_{n+1:03}_registered_arm_indices.png');Image.fromarray(target).save(o/f'{form}_{n+1:03}.png');Image.fromarray(allowed.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_allowed_mask.png');Image.fromarray(patch.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_patch_mask.png');Image.fromarray(ring.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_gun_ring_clear_mask.png')
            occupied=target[:,:,3]>0;lab,nc=label(occupied,np.ones((3,3),int));components=sorted([int((lab==j).sum())for j in range(1,nc+1)],reverse=True);contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&occupied&~guard
            rows.append({'form':form,'ref':n+1,'body_ref':n,'source_sha256':z.sha,'changed_pixels':int(np.any(target!=before,axis=2).sum()),'connected_components_8way':components,'barrel_adjacent_body_pixels':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(contact))],'new_head_preserved_beside_barrel':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(protected_head))],'source_supported_contour_samples':edge,'body_outside_patch_exact':True,'face_exact':True,'barrel_guard_exact':True});pics.extend([(f'{n} new body',Image.fromarray(before)),(f'{n+1} new arm fixed muzzle',Image.fromarray(target))])
        page(pics,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=6)
    write(o/'report.json',{'parent_sha256':sha(P.read_bytes()),'source_sha256':z.sha,'page':z.page,'scale':.125,'alpha_threshold':128,'rows':rows,'visual_review_pending':True,'packed':False,'runtime_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
