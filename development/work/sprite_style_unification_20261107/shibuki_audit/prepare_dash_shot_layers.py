"""대시 사격 후보의 새 팔을 아머 소유 층으로 분리, 부분 조합 검사."""
from pathlib import Path
import json,sys,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from prepare_dash_body_layers import P
SOURCES={68:'dash_shot_page01_registered03',70:'dash_shot_page01_registered03',72:'dash_shot_page02_registered01',76:'dash_shot_page02_registered01'}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='dash_shot_layers01');z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh isolated output');o.mkdir();a=Archive(P.read_bytes());rows=[];pics=[]
    for n,folder in SOURCES.items():
        d=H/folder;body={b:np.array(Image.open(H/f'dash_body_layers01/{n-1:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}
        layers={0:np.array(Image.open(d/f'base_{n:03}_indices.png'))};allowed=np.array(Image.open(d/f'fourth_{n:03}_allowed_mask.png'))>0;ring=np.array(Image.open(d/f'fourth_{n:03}_gun_ring_clear_mask.png'))>0;guard=np.array(Image.open(H/f'dash_barrel_guard02/{n:03}_mask.png'))>0
        source=np.array(Image.open(d/f'fourth_{n:03}_registered_arm_indices.png'))
        for b in (5,6,7,8):
            ar=body[b].copy();ar[allowed]=0
            if b==7:ar[allowed&~guard&~ring]=source[allowed&~guard&~ring]
            ar[guard]=0;layers[b]=ar
        target=Image.open(d/f'fourth_{n:03}.png').convert('RGBA');need(compose(a,layers,15).tobytes()==target.tobytes(),'Layer split changes full target');need(a.rgba(layers[0]).tobytes()==Image.open(d/f'base_{n:03}.png').convert('RGBA').tobytes(),'Base indexed mismatch')
        for b,v in layers.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
        for arm in (1,2):
            for mask in range(16):
                im=compose(a,layers,mask,arm);need(np.array_equal(np.array(im)[guard],np.array(a.rgba(layers[0]))[guard]),'Partial armor changes gun')
        page([(f'{n} mask{mask:X}',compose(a,layers,mask))for mask in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=3)
        rows.append({'ref':n,'body_ref':n-1,'source':folder,'source_report_sha256':sha((d/'report.json').read_bytes()),'layer_pixels':{str(b):int((ar>0).sum())for b,ar in layers.items()},'full_exact':True,'base_exact':True,'all_32_partial_gun_exact':True})
        pics.extend([(f'{n} base',compose(a,layers,0)),(f'{n} arm only',compose(a,layers,4)),(f'{n} full',compose(a,layers,15))])
    for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,15)[0],o/f'ownership_{i//6:02}.png',cols=3,scale=4)
    write(o/'report.json',{'rows':rows,'parent_sha256':sha(P.read_bytes()),'partial_combinations':len(rows)*32,'native_cpu_verified':False,'packed':False,'visual_review_pending':True});print(json.dumps({'refs':len(rows),'partial_combinations':len(rows)*32}))
if __name__=='__main__':main()
