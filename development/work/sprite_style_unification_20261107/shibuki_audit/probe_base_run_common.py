"""새 이동 머리 공유와 장식 소유/의상 외곽을 검토한다. ARC 미작성."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from probe_dash_common_head import poly
def main():
    o=H/'base_run_common_probe01';need(not o.exists(),'Fresh output');o.mkdir();d=H/'base_run_native01';a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());src=np.array(Image.open(H/'base_run_followup02/generated.png'));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.int32);y,x=np.indices((384,384));x-=160;y-=160;rows=[];pics=[]
    for n,(ex,ey)in{3:(-5,-9),11:(-12,-9),19:(-8,-9)}.items():
        base=np.array(Image.open(d/f'base_{n:03}_indices.png'));raw=np.array(Image.open(d/f'fourth_{n:03}_indices.png'));foot=[]
        if n==3:
            for wx in range(10,16):
                b=src[(22+36)*8+512:(23+36)*8+512,(wx+32)*8:(wx+33)*8];m=b[:,:,3]>=128;q=1+((b[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2);v,c=np.unique(q[m],return_counts=True);idx=int(v[c.argmax()]);need(m.sum()>=28,'Source sole insufficient');need(raw[182,wx+160]==0,'Source sole expected zero');raw[182,wx+160]=idx;foot.append({'world':[wx,22],'source_opaque':int(m.sum()),'source_mode':idx,'histogram':dict(zip(map(str,v),map(int,c)))})
        region=poly([(ex-12,ey-18),(ex+16,ey-18),(ex+16,ey-7),(ex+34,ey-2),(ex+34,ey+5),(ex+17,ey+8),(ex+5,ey+3),(ex-6,ey+3),(ex-12,ey-3)]);face=(x>=ex-4)&(x<=ex+4)&(y>=ey-3)&(y<=ey+3);common=region&(np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13])));dec=(x>=ex+5)&(x<ex+21)&(y>=ey-13)&(y<ey+3)&region;common|=dec;over=raw.copy();over[common]=0;over[dec]=raw[dec];edge=(base>0)&(over==0)&(~common|dec)
        head=np.where(dec,over,0).astype(np.uint8);rest=np.where(~dec,over,0).astype(np.uint8);result=a.rgba(base);result.alpha_composite(a.rgba(rest,16));result.alpha_composite(a.rgba(head,16));result.save(o/f'fourth_{n:03}.png')
        for name,v in(('base_indices',base),('raw_fourth_indices',raw),('head_indices',head),('rest_indices',rest)):Image.fromarray(v).save(o/f'{n:03}_{name}.png')
        for name,m in(('common',common),('decoration',dec),('uncovered_base',edge)):Image.fromarray(m.astype(np.uint8)*255).save(o/f'{n:03}_{name}_mask.png')
        ys,xs=np.nonzero(head);bbox=[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)];ys,xs=np.nonzero(edge);outside=[{'world':[int(px-160),int(py-160)],'base_index':int(base[py,px])}for py,px in zip(ys,xs)];rows.append({'ref':n,'new_common_head_opaque':int(np.count_nonzero(base[common])),'head_bbox':bbox,'uncovered_base_pixels':outside,'source_sole_cells':foot,'old_head_copied':False,'whole_body_resized':False,'eye_original_delta':{3:[0,0],11:[-1,0],19:[0,-1]}[n]});pics.extend([(f'{n} new raw Fourth',a.rgba(raw,16)),(f'{n} new common head / edges pending',result)])
    page(pics,a.composite(0,15)[0],o/'comparison.png',cols=2,scale=5);write(o/'report.json',{'candidate_only':True,'rows':rows,'edge_pixels_not_fixed':True,'part_ownership_pending':True,'source_sole_note':'포스3의최근접샘플에서빠진원화바닥6셀만각8x8실제표본최빈색으로등록. 기본3과원발바닥x10..15/y22에동일하게접지.추측색칠/행늘림아님.','body_original_foot_positions_preserved':True,'gameplay_verified':False});print(json.dumps([{'ref':r['ref'],'uncovered':len(r['uncovered_base_pixels']),'head_bbox':r['head_bbox']}for r in rows]))
if __name__=='__main__':main()
