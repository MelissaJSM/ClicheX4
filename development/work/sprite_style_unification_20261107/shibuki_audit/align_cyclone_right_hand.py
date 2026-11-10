"""새 손/손목 끝만 (+1,-1) 등록. 확대·늘림·빈 영역 채움 없음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from prepare_lowhp_final import compose
def main():
    source=H/'double_cyclone_layers_probe01';out=H/'double_cyclone_layers_probe02';need(not out.exists(),'Fresh output required');out.mkdir()
    arc=Archive((H/'prepared_air01/PL00_U.ARC').read_bytes());old={b:np.array(Image.open(source/f'098_bank{b}_indices.png'))for b in(0,5,6,7,8)};new={b:v.copy()for b,v in old.items()}
    yy,xx=np.indices((384,384));region=(xx>=176)&(xx<186)&(yy>=148)&(yy<=158);report=[]
    for b in(0,5,6,7,8):
        v=old[b];mask=region&(v>0);y,x=np.nonzero(mask);new[b][mask]=0
        need(not np.any(new[b][y-1,x+1]),'Translated hand overlaps external source pixels')
        new[b][y-1,x+1]=v[y,x]
        Image.fromarray(new[b]).save(out/f'098_bank{b}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/f'098_bank{b}_registration_mask.png')
        report.append({'bank':b,'source_index_sha256':sha(v.tobytes()),'after_index_sha256':sha(new[b].tobytes()),'moved_pixels':len(x),'translation':[1,-1],'moved_index_values_exact':True})
    for name,mask in(('base',0),('fourth',15)):
        page([('before hand registration',compose(arc,old,mask)),('new hand (+1,-1)',compose(arc,new,mask))],arc.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=7)
    page([(f'mask{m:X}',compose(arc,new,m))for m in range(16)],arc.composite(0,15)[0],out/'partial.png',cols=4,scale=4)
    write(out/'report.json',{'passed':True,'scope':'같은 새 손/손목의 1px 평행등록. 팔/몸통 크기나 길이를 변경하지 않음.','region_world':[16,-12,26,-1],'moved':report,'new_pixels_drawn':0,'scaling':False,'root_review_pending':True})
if __name__=='__main__':main()
