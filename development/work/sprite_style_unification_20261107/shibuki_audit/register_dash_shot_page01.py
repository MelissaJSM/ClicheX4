"""첫 대시사격4의 새 앞팔만 고정 배율/의미마스크로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from prepare_dash_body_layers import rect,P
from probe_dash_common_head import poly
SOURCE_SHA='dec43392dfbbbca1b0434add7faf772ace1f2b5c4c0d51091c651707bb1bfee9'
def masks(n,mx,my):
    removed={67:[(-17,-2),(-7,-2),(-3,4),(-5,10),(-12,12),(-17,7)],69:[(-20,3),(-9,3),(-6,8),(-8,16),(-16,18),(-21,12)]}[n]
    sx,sy={67:(-6,-1),69:(-9,4)}[n]
    added=[(mx+7,my-3),(sx-6,my-3),(sx+3,sy-3),(sx+3,sy+5),(sx-6,sy+8),(mx+7,my+7)]
    face=rect({67:(-12,-10,0,-1),69:(-15,-5,-3,4)}[n])
    return (poly(removed)|poly(added))&~face,face
def main():
    d=H/'dash_shot_inputs02/page01';o=H/'dash_shot_native02';need(not o.exists(),'Fresh output required');o.mkdir();src=d/'generated.png';need(sha(src.read_bytes())==SOURCE_SHA,'Wrong source');im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Wrong size');sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));a=Archive(P.read_bytes());gmdata=json.loads((H/'dash_barrel_guard02/report.json').read_text('utf8'));rows=[]
    for row,(form,pal,mask)in enumerate((('base',0,0),('fourth',16,15))):
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);pics=[]
        for col,n in enumerate((67,69)):
            cell=sample[row*64:(row+1)*64,col*96:(col+1)*96];q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
            source=np.zeros((384,384),np.uint8);source[124:188,112:208]=q;Image.fromarray(source).save(o/f'{form}_{n+1:03}_source_indices.png')
            body={b:np.array(Image.open(H/f'dash_body_layers01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};before=np.array(compose(a,body,mask));gm=next(r for r in gmdata['rows']if r['body_ref']==n and r['form']==form);mx,my=gm['muzzle_world'];patch,face=masks(n,mx,my)
            # Only the back/under-grip side of the placed original gun is art
            # territory. A changed generated barrel may not expand its guard.
            yy,xx=np.indices(source.shape);patch&=(xx>=160+mx+8)
            gun=np.array(Image.open(H/f'dash_barrel_guard02/{n+1:03}_indices.png'));guard=np.array(Image.open(H/f'dash_barrel_guard02/{n+1:03}_mask.png'))>0
            target=before.copy();target[patch]=np.array(a.rgba(source,pal))[patch];target[guard]=np.array(a.rgba(gun))[guard];allowed=patch|guard
            # The generated gun added an outer ring behind the locked casing.
            # Remove only that ring above the first real new palm skin row.
            # This is native module/transparent-guard registration, not a body
            # redraw. The original new body has no opaque texel in this box.
            band=(xx>=160+mx+8)&(xx<160+mx+12)&(yy>=160+my-4)&(yy<160+my+5)
            skin=band&np.isin(source,[12,13]if form=='base'else[9]);sy,_=np.nonzero(skin);need(len(sy)>0,'No source hand under casing')
            ring=band&(yy<sy.min())&~guard;need(not np.any(before[:,:,3][ring]),'Gun restoration reaches existing body')
            removed_ring=[[int(x)-160,int(y)-160,int(source[y,x])]for y,x in zip(*np.nonzero(ring&(source>0)))]
            target[ring]=0;allowed|=ring
            need(np.array_equal(target[~allowed],before[~allowed]),'Changed outside arm');need(np.array_equal(target[face&~guard],before[face&~guard]),'Face changed');need(np.array_equal(target[guard],np.array(a.rgba(gun))[guard]),'Casing changed')
            if form=='base':
                indices=body[0].copy();indices[patch]=source[patch];indices[guard]=gun[guard];indices[ring]=0;Image.fromarray(indices).save(o/f'base_{n+1:03}_indices.png')
            Image.fromarray(target).save(o/f'{form}_{n+1:03}.png');Image.fromarray(patch.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_patch_mask.png');Image.fromarray(allowed.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_allowed_mask.png');Image.fromarray(ring.astype(np.uint8)*255).save(o/f'{form}_{n+1:03}_gun_ring_clear_mask.png')
            occupied=target[:,:,3]>0;lab,nc=label(occupied,np.ones((3,3),int));components=sorted([int((lab==j).sum())for j in range(1,nc+1)],reverse=True)
            contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&occupied&~guard
            rows.append({'form':form,'ref':n+1,'body_ref':n,'source_sha256':SOURCE_SHA,'patch_pixels':int(patch.sum()),'changed_pixels':int(np.any(target!=before,axis=2).sum()),'connected_components_8way':components,'barrel_adjacent_body_pixels':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(contact))],'removed_generated_barrel_ring':removed_ring,'body_outside_patch_exact':True,'face_exact':True,'barrel_guard_exact':True})
            pics.extend([(f'{n} new body',Image.fromarray(before)),(f'{n+1} new arm at original muzzle',Image.fromarray(target))])
        page(pics,a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=6)
    (d/'prompt_used.txt').write_text((d/'prompt.txt').read_text('utf8'),encoding='utf8');write(d/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':'exec-dbd80dd6-1a94-4efa-9f6f-40c34d0795ef.png','source_sha256':SOURCE_SHA,'prompt_sha256':sha((d/'prompt_used.txt').read_bytes()),'native_registration':'dash_shot_native02','packed':False})
    write(o/'report.json',{'parent_sha256':sha(P.read_bytes()),'source_sha256':SOURCE_SHA,'scale':0.125,'alpha_threshold':128,'rows':rows,'scope':'첫2사격×두의상 팔 의미영역만. 최종 아머레이어·타일 패킹은 미완료.','game_modified':False,'visual_review_pending':True});print(json.dumps(rows))
if __name__=='__main__':main()
