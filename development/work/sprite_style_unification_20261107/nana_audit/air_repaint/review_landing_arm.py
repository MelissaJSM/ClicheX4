"""착지 사격의 새 원화 소매 영역을 원래 총구 및 새 몸체와 대조한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from review_all_bodies import source as body_source

def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'landing54_probe_v2';need(not out.exists(),'Fresh output');out.mkdir()
    n=54;body=np.array(Image.open(body_source(53)/'base_053.png'));src=np.array(Image.open(D/'basic_firing_c_registered_v1/base_054.png'));gun=np.array(Image.open(D/'fire_constraints/barrel_054.png'))
    yy,xx=np.indices(body.shape);x=xx-160;y=yy-160
    # Front sleeve + wrist only. These bounds were inspected on the new
    # authored source. No pixel is drawn, recoloured, stretched or moved.
    arm_mask=(x>=-19)&(x<=-5)&(y>=-7)&(y<=-3)
    arm=np.where(arm_mask,src,0).astype(np.uint8)
    # Remove the held-down front forearm of body53; preserve head, rear arm,
    # skirt, legs and all boot/ground contacts outside this local region.
    remove=(x<=-4)&(y>=-6)&(y<=3);rest=body.copy();rest[remove]=0
    target=np.where(arm,arm,rest).astype(np.uint8)
    gy,gx=np.nonzero(gun);window=(xx>=gx.min())&(xx<=gx.min()+7)&(yy>=gy.min())&(yy<=gy.max());target[window]=gun[window]
    allowed=remove|arm_mask|window;need(np.array_equal(target[~allowed],body[~allowed]),'Unrelated body exact');need(np.array_equal(target[window],gun[window]),'Complete gun window exact')
    labels,count=label(target>0,np.ones((3,3)));contacts=int(np.count_nonzero(binary_dilation(arm>0,np.ones((3,3)))&(rest>0)))
    for name,idx in [('merged',target),('new_sleeve',arm),('remaining_body',rest)]:Image.fromarray(idx).save(out/f'{name}_054.png');a.rgba(idx).save(out/f'{name}_054_rgba.png')
    helper.grid([('landing shot54',[('대기',a.composite(0)[0]),('새 몸체53',a.rgba(body)),('새 사격 원화',a.rgba(src)),('동일 원점 팔/원 총',a.rgba(target))])],out/'comparison.png',8)
    write(out/'manifest.json',{'ref':54,'source_arc_sha256':sha(a.data),'source_art_sha256':'e2912a10154a6548cefe50c3e674fd2c13c77ebe16fcf6d233e4c3a0944d06bf','rigid_shift':[0,0],'source_sleeve_and_wrist':True,'source_hand_joins_original_grip':True,'gun_window_exact':True,'non_arm_region_exact':True,'alpha_components_8':count,'sleeve_body_contact_pixels':contacts,'native_packed':False});print(count,contacts)
if __name__=='__main__':main()
