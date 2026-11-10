"""새 이동15몸체의 부분 아머 소유 분리. 원화·ARC는 변경하지 않는다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts
from prepare_lowhp_final import compose
from probe_dash_common_head import poly
from prepare_dash_body_layers import rect
from compose_base_run_shots import REMOVED
ARM={3:(-13,-3,3,13),5:(-19,-4,-3,12),7:(-19,-3,-3,13),9:(-17,-3,-1,13),11:(-20,-4,-4,12),13:(-17,-4,-1,12),15:(-17,-4,-1,12),17:(-16,-2,0,14),19:(-11,-1,5,15),21:(-14,-2,2,14),23:(-16,-3,0,13),25:(-16,-3,0,13),27:(-16,-4,0,12),29:(-18,-5,-2,11),31:(-18,-5,-2,11)}
LEG={
3:[(-8,8),(0,11),(5,9),(9,8),(20,20),(20,24),(-10,24)],
5:[(-9,8),(-1,10),(6,8),(14,12),(20,24),(-20,24),(-17,18)],
7:[(-9,8),(-1,10),(6,8),(15,12),(20,24),(-20,24),(-17,18)],
9:[(-9,8),(0,10),(6,8),(16,14),(20,24),(-20,24),(-16,17)],
11:[(-12,8),(-3,9),(4,6),(7,7),(11,13),(8,24),(-15,24)],
13:[(-11,8),(-3,9),(3,7),(8,11),(10,24),(-15,24)],
15:[(-11,8),(-3,9),(3,7),(8,11),(10,24),(-15,24)],
17:[(-10,8),(-2,10),(5,8),(16,13),(20,24),(-20,24),(-17,18)],
19:[(-9,9),(-1,9),(6,9),(20,20),(15,24),(-20,24),(-20,18)],
21:[(-9,9),(-1,10),(6,9),(21,17),(21,24),(-20,24),(-20,18)],
23:[(-10,8),(-1,10),(6,8),(18,17),(19,24),(-20,24),(-18,17)],
25:[(-10,8),(-1,10),(6,8),(18,16),(19,24),(-20,24),(-18,17)],
27:[(-11,8),(-3,9),(3,7),(9,12),(13,24),(-16,24)],
29:[(-11,8),(-3,9),(3,7),(17,17),(19,24),(-17,24)],
31:[(-11,8),(-2,10),(5,8),(17,15),(20,24),(-20,24),(-18,17)]}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='base_run_body_layers02');z=ap.parse_args();out=(H/z.output).resolve();need(out.is_relative_to(H.resolve())and not out.exists(),'Fresh output required');out.mkdir()
    p=H/'prepared_dash_base01/PL00_U.ARC';need(sha(p.read_bytes())=='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b','Parent changed');a=Archive(p.read_bytes());d=H/'base_run_common01';meta=json.loads((d/'report.json').read_text('utf8'));rows=[];heads={};pics=[]
    for m in meta['rows']:
        n=m['ref'];base=np.array(Image.open(d/f'{n:03}_base_indices.png'));head=np.array(Image.open(d/f'{n:03}_head_indices.png'));rest=np.array(Image.open(d/f'{n:03}_rest_indices.png'));owner=np.full(base.shape,6,np.uint8);owner[poly(LEG[n])]=8;owner[poly(REMOVED[n])]=7
        layers={0:base,5:head};layers.update({b:np.where(owner==b,rest,0).astype(np.uint8)for b in(6,7,8)});full=compose(a,layers,15)
        need(full.tobytes()==Image.open(d/f'fourth_{n:03}.png').convert('RGBA').tobytes(),'Ownership changed full artwork')
        for b,ar in layers.items():Image.fromarray(ar).save(out/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(owner).save(out/f'{n:03}_ownership.png');full.save(out/f'fourth_{n:03}.png');a.rgba(base).save(out/f'base_{n:03}.png');heads[n]=bytes.fromhex(m['head_record_hex']);heads[n+1]=heads[n]
        for arm in(1,2):
            for mask in range(16):need(compose(a,layers,mask,arm).size==(384,384),'Partial canvas changed')
        page([(f'{n} mask{mask:X}',compose(a,layers,mask))for mask in range(16)],a.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
        pics.extend([(f'{n} head only',compose(a,layers,1)),(f'{n} arm only',compose(a,layers,4)),(f'{n} body+legs',compose(a,layers,10)),(f'{n} full',full)])
        rows.append({'ref':n,'arm_polygon':REMOVED[n],'arm_polygon_source_sha256':sha((H/'compose_base_run_shots.py').read_bytes()),'leg_polygon':LEG[n],'head_record_hex':heads[n].hex(),'source_new_common_report_sha256':sha((d/'report.json').read_bytes()),'base_exact':True,'full_exact':True,'layer_pixels':{str(b):int((ar>0).sum())for b,ar in layers.items()},'layer_raw_sha256':{str(b):sha(ar.tobytes())for b,ar in layers.items()}})
    _,slack=repack_parts(a.c,5,heads)
    for i in range(0,len(pics),12):page(pics[i:i+12],a.composite(0,15)[0],out/f'ownership_{i//12:02}.png',cols=4,scale=4)
    write(out/'report.json',{'parent_sha256':sha(a.data),'rows':rows,'part_ownership_policy':'새 기본 머리 공통·포스 장식 Head·앞소매 Arm·상의/뒷소매 Body·하체 Leg. 소유 분리만 수행해 완성 폼 픽셀은 입력과 동일.','partial_cases':480,'head_dry_run_shot_aliases_slack':slack,'visual_review_pending':True,'shot_art_pending':True,'arc_written':False,'runtime_verified':False});print(json.dumps({'refs':len(rows),'partial_cases':480,'head_slack':slack}))
if __name__=='__main__':main()
