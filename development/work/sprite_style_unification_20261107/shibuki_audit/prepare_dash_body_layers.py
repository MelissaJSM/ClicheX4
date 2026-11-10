"""10개 새 대시 몸체를 고정 아머 소유로 분리한다. 전체 디스크 쓰기 없음."""
from pathlib import Path
import json,sys,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts
from prepare_lowhp_final import compose
from probe_dash_common_head import poly,REFS,P,D
ARM={67:(-17,-2,-1,14),69:(-20,3,-4,19),71:(-26,7,-10,23),75:(-25,8,-9,24),77:(-20,1,-4,17),79:(-16,0,0,16),81:(-17,0,-1,16),83:(-17,-3,-1,13),93:(-19,-17,-3,-1),94:(-20,0,-4,16)}
LEG={67:[(-9,10),(1,11),(6,8),(10,11),(20,20),(20,24),(-9,24)],69:[(-10,13),(1,12),(7,11),(18,19),(18,24),(-10,24)],71:[(-11,15),(-1,14),(8,14),(18,19),(18,24),(-13,24)],75:[(-10,15),(-2,14),(8,15),(16,20),(16,24),(-12,24)],77:[(-9,11),(1,12),(7,10),(20,21),(20,24),(-10,24)],79:[(-9,9),(0,10),(6,8),(16,20),(16,24),(-10,24)],81:[(-11,8),(-3,10),(3,9),(9,7),(17,23),(-18,23)],83:[(-9,8),(-3,10),(2,10),(5,9),(13,23),(-14,23)],93:[(-10,8),(1,8),(4,15),(2,21),(-6,21),(-12,14)],94:[(-9,13),(-1,12),(5,13),(16,22),(16,26),(-5,23),(-12,18)]}
def rect(box):
    x0,y0,x1,y1=box;a=np.zeros((384,384),bool);a[y0+160:y1+160,x0+160:x1+160]=True;return a
def main():
    o=H/'dash_body_layers01';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());q=H/'dash_common_head_probe01';meta=json.loads((q/'probe.json').read_text('utf8'));rows=[];head_records={};allpics=[]
    for n in REFS:
        base=np.array(Image.open(D/f'base_{n:03}_indices.png'));head=np.array(Image.open(q/f'{n:03}_head_indices.png'));rest=np.array(Image.open(q/f'{n:03}_rest_indices.png'))
        owner=np.full(base.shape,6,np.uint8);owner[poly(LEG[n])]=8;owner[rect(ARM[n])]=7
        layers={0:base,5:head};layers.update({b:np.where(owner==b,rest,0).astype(np.uint8)for b in(6,7,8)})
        full=compose(a,layers,15);need(full.tobytes()==Image.open(q/f'{n:03}_fourth.png').convert('RGBA').tobytes(),'Split changes composed target')
        m=next(r for r in meta['rows']if r['ref']==n);x0,y0,x1,y1=m['head_bbox_world'];need(x1-x0<=16 and y1-y0<=16,'Head exceeds one tile')
        # A new single record fits the original bank after replacing duplicate
        # old records. No bank boundary movement and no old head copying.
        head_records[n]=struct.pack('<BBbb',0,10,x0,y0)
        for b,v in layers.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(owner).save(o/f'{n:03}_ownership.png');full.save(o/f'{n:03}_fourth.png');a.rgba(base).save(o/f'{n:03}_base.png')
        for arm in(1,2):
            for mask in range(16):need(compose(a,layers,mask,arm).size==(384,384),'Unexpected canvas')
        page([(f'{n} mask{mask:X}',compose(a,layers,mask))for mask in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=3)
        rows.append({'ref':n,'layer_pixels':{str(b):int((v>0).sum())for b,v in layers.items()},'layer_raw_sha256':{str(b):sha(v.tobytes())for b,v in layers.items()},'head_record_hex':head_records[n].hex(),'head_bbox_world':m['head_bbox_world'],'source_base_exact':True,'full_target_exact':True})
        allpics.extend([(f'{n} head only',compose(a,layers,1)),(f'{n} body/arm/leg',compose(a,layers,14)),(f'{n} full',full)])
    _,slack=repack_parts(a.c,5,head_records)
    for i in range(0,len(allpics),9):page(allpics[i:i+9],a.composite(0,15)[0],o/f'ownership_{i//9:02}.png',cols=3,scale=4)
    write(o/'registration.json',{'parent_sha256':sha(P.read_bytes()),'rows':rows,'head_bank_dry_run_remaining_bytes':slack,'part_ownership_policy':'새 기본 머리/얼굴 공통, 포스 새 장식 Head, 앞팔 Arm, 망토/상의/뒷소매 Body, 하체/부츠 Leg.','body_shoot_shared_pack_pending':True,'all_partial_visual_review_pending':True,'bank_boundary_changed':False,'resource_written':False,'runtime_verified':False})
    print(json.dumps({'refs':len(rows),'head_bank_slack':slack,'partial_combinations':320}))
if __name__=='__main__':main()
