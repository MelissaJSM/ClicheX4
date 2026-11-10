"""새 원화의 모자/꽃 교체 영역을 Head 파츠로 재분류하는 미리보기."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from inspect_air_layers import P,REFS
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from prepare_air_body_layers import rect
from prepare_lowhp_final import compose
from probe_air_body_capacity import candidates

def main():
    out=H/'air_head_ownership03';need(not out.exists(),'Fresh output required');out.mkdir();a=Archive(P.read_bytes());rows=[];pics=[]
    boxes={33:(0,-20,10,-6),35:(0,-20,10,-6),37:(0,-20,10,-6),39:(4,-23,11,-10),41:(4,-23,11,-9),43:(0,-21,8,-11),45:(0,-20,10,-6),47:(0,-20,10,-6),49:(0,-20,10,-6),51:(0,-16,10,-2),53:(0,-17,10,-3)}
    for n in sorted(REFS):
        before={b:np.array(Image.open(H/f'air_body_layers01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};new={b:v.copy()for b,v in before.items()};m=rect(boxes[n]);moved=[]
        for b in(8,7,6):
            sel=m&(new[b]>0);yy,xx=np.nonzero(sel)
            for y,x in zip(yy,xx):moved.append([int(x)-160,int(y)-160,b,int(new[b][y,x])])
            new[5][sel]=new[b][sel];new[b][sel]=0
        need(compose(a,new,15).tobytes()==compose(a,before,15).tobytes(),'Part ownership changed full rendering')
        for b,v in new.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png')
        for mask in(0,1,14,15):compose(a,new,mask).save(out/f'{n:03}_mask{mask:02}.png')
        templates=candidates(a.c,5,new[5]);y,x=np.nonzero(new[5]);rows.append({'ref':n,'moved_pixels':moved,'head_bbox':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'existing_single_part_templates':[v.hex()for v in templates],'full_rgba_exact':True,'base_indices_exact':np.array_equal(new[0],before[0])})
        pics.extend([(f'{n} old head-only',compose(a,before,1)),(f'{n} ownership head-only',compose(a,new,1)),(f'{n} full unchanged',compose(a,new,15))])
        if n in(33,39,41,43):page([(f'{n} mask{mask:X}',compose(a,new,mask))for mask in range(16)],a.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
    for i in range(0,len(pics),12):page(pics[i:i+12],a.composite(0,1)[0],out/f'comparison_{i//12:02}.png',cols=3,scale=4)
    write(out/'report.json',{'candidate_only':True,'full_visual_pixels_changed':0,'source_parent_sha256':sha(P.read_bytes()),'rows':rows,'resource_written':False,'all_partial_visual_review_pending':True})
    print(json.dumps([{'ref':r['ref'],'head_bbox':r['head_bbox'],'single_templates':len(r['existing_single_part_templates'])}for r in rows]))
if __name__=='__main__':main()
