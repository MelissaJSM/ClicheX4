"""첫 세 이동 자세의 새 원화 경계와 부분 아머 소유를 검토한다. ARC 쓰기 없음."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts
from prepare_lowhp_final import compose
from probe_dash_common_head import poly
from prepare_dash_body_layers import rect
ARM={3:(-13,-3,3,13),11:(-20,-4,-4,12),19:(-11,-1,5,15)}
LEG={3:[(-8,8),(0,11),(5,9),(9,8),(20,20),(20,24),(-10,24)],11:[(-12,8),(-3,9),(4,6),(7,7),(11,13),(8,24),(-15,24)],19:[(-9,9),(-1,9),(6,9),(20,20),(15,24),(-20,24),(-20,18)]}
def main():
    o=H/'base_run_layers_probe01';need(not o.exists(),'Fresh output');o.mkdir();p=H/'prepared_dash_base01/PL00_U.ARC';need(sha(p.read_bytes())=='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b','Parent changed');a=Archive(p.read_bytes());d=H/'base_run_common_probe01';src=np.array(Image.open(H/'base_run_followup02/generated.png'));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.int32);rows=[];pics=[];heads={}
    for col,n in enumerate((3,11,19)):
        base=np.array(Image.open(d/f'{n:03}_base_indices.png'));raw=np.array(Image.open(d/f'{n:03}_raw_fourth_indices.png'));common=np.array(Image.open(d/f'{n:03}_common_mask.png'))>0;dec=np.array(Image.open(d/f'{n:03}_decoration_mask.png'))>0
        if n==19:
            # Flowing new base hair's outer tip; not a sleeve/garment mask.
            yy,xx=np.indices(base.shape);common|=(xx>=173)&(yy>=157)&(yy<=163)&np.isin(base,[0,2,5,8,14,15]);dec&=~((xx>=173)&(yy>=157))
        over=raw.copy();over[common]=0;over[dec]=raw[dec];edge=(base>0)&(over==0)&(~common|dec);changes=[]
        for py,px in zip(*np.nonzero(edge)):
            wx,wy=int(px)-160,int(py)-160;cell=src[512+(wy+36)*8:512+(wy+37)*8,col*512+(wx+32)*8:col*512+(wx+33)*8];m=cell[:,:,3]>=128;coverage=int(m.sum());bidx=int(base[py,px])
            if coverage>=8:
                q=1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2);v,c=np.unique(q[m],return_counts=True);idx=int(v[c.argmax()]);method='new_source_cell_opaque_mode';hist=dict(zip(map(str,v),map(int,c)))
            else:
                # Tiny new-base contour/ornament pieces cannot be erased by
                # PS1 overlays. Local material translation only; no old master.
                need(bidx in(1,2,15),'Unexpected unsampled interior');idx={1:2,2:2,15:1}[bidx];method='new_base_local_contour_material';hist={}
            over[py,px]=idx;changes.append({'world':[wx,wy],'base_index':bidx,'fourth_index':idx,'source_opaque':coverage,'method':method,'source_histogram':hist})
        need(not np.any((base>0)&(over==0)&(~common|dec)),'Uncovered base costume edge')
        owner=np.full(base.shape,6,np.uint8);owner[poly(LEG[n])]=8;owner[rect(ARM[n])]=7;owner[dec]=5
        layers={0:base};layers.update({b:np.where(owner==b,over,0).astype(np.uint8)for b in(5,6,7,8)})
        full=compose(a,layers,15);rawimg=a.rgba(raw,16);baseimg=a.rgba(base);full.save(o/f'fourth_{n:03}.png');baseimg.save(o/f'base_{n:03}.png')
        for bank,v in layers.items():Image.fromarray(v).save(o/f'{n:03}_bank{bank}_indices.png')
        for name,m in(('common',common),('decoration',dec),('owner',owner)):Image.fromarray(m.astype(np.uint8)*(255 if m.dtype==bool else 1)).save(o/f'{n:03}_{name}_mask.png')
        ys,xs=np.nonzero(layers[5]);bbox=[int(xs.min())-160,int(ys.min())-160,int(xs.max())-159,int(ys.max())-159];need(bbox[2]-bbox[0]<=16 and bbox[3]-bbox[1]<=16,'Head tile exceeds fixed16');heads[n]=struct.pack('<BBbb',0,10,bbox[0],bbox[1])
        for arm in(1,2):
            for mask in range(16):need(compose(a,layers,mask,arm).size==(384,384),'Invalid partial canvas')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=4)
        pics.extend([(f'{n} raw new Fourth',rawimg),(f'{n} common head / local material',full)])
        rows.append({'ref':n,'head_bbox':bbox,'source_boundary_registration':changes,'layer_pixels':{str(b):int((v>0).sum())for b,v in layers.items()},'base_actual_source_exact':True,'sole_height':int(np.nonzero(base)[0].max())-160,'head_record_hex':heads[n].hex(),'old_head_or_body_copied':False})
    _,slack=repack_parts(a.c,5,heads);page(pics,a.composite(0,15)[0],o/'comparison.png',cols=2,scale=5)
    write(o/'report.json',{'candidate_only':True,'rows':rows,'head_bank_dry_run_slack':slack,'partial_cases':96,'partial_visual_review_pending':True,'all_new_source_hash':'4937d67682025bb9a2b940e9b6fa009e0c816666bffce654e7d93cfc6bc12b30','policy':'새 기본 머리 공통+새 포스 장식1타일, 새 앞소매 Arm/상의 Body/하체 Leg. 원화 8x8 실제 표본 또는 작은 새 외곽의 재질 대응만 사용. 구형 본체·머리 덮기 없음.','arc_written':False,'whole_body_resized':False,'original_palette_or_timing_changed':False,'runtime_verified':False});print(json.dumps({'head_bank_slack':slack,'boundary_cells':[len(r['source_boundary_registration'])for r in rows],'partial_cases':96}))
if __name__=='__main__':main()
