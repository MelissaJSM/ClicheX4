"""새 공중 몸체22표시를 기본/포스 파츠로 분리. 입력·게임은 수정하지 않는다."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
import numpy as np
from inspect_air_layers import arrays,REFS,P
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from prepare_lowhp_final import compose

def polygon(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def rect(box):
    x0,y0,x1,y1=box;v=np.zeros((384,384),bool);v[y0+160:y1+160,x0+160:x1+160]=True;return v
def ownership(n):
    # Foreground shooting forearm follows the existing Arm ownership; the
    # mantle/other upper sleeve remains Body. No palette or pose transformation.
    arm={33:(-16,-8,0,8),35:(-16,-8,0,8),37:(-18,-17,-2,-1),39:(-14,-26,2,-10),41:(-18,-25,-2,-9),43:(-20,-23,-4,-7),45:(-15,-10,1,6),47:(-15,-9,1,7),49:(-14,-7,2,9),51:(-14,-4,2,12),53:(-15,-6,1,10)}[n]
    legs={33:[(-9,7),(3,7),(5,18),(-10,18)],35:[(-9,6),(4,6),(4,20),(-8,20)],37:[(-11,5),(2,5),(5,20),(-8,20)],39:[(-11,0),(1,0),(6,16),(-3,16),(-12,9)],41:[(-11,5),(3,5),(8,20),(-3,20),(-11,12)],43:[(-10,6),(3,6),(8,18),(-2,18),(-10,11)],45:[(-9,7),(4,7),(7,21),(-3,21),(-10,12)],47:[(-9,7),(4,7),(7,22),(-2,22),(-10,13)],49:[(-9,7),(3,7),(13,23),(-12,23)],51:[(-8,7),(3,7),(15,23),(-14,23)],53:[(-9,7),(3,7),(15,23),(-14,23)]}[n]
    owner=np.full((384,384),6,np.uint8);owner[polygon(legs)]=8;owner[rect(arm)]=7;return owner

def main():
    d=H/'air_common_head_probe03';meta=json.loads((d/'probe.json').read_text('utf8'));a=Archive(P.read_bytes());o=H/'air_body_layers01';need(not o.exists(),'Fresh output only');o.mkdir();rows=[];pics=[]
    for n in sorted(REFS):
        base,_=arrays(n);head=np.array(Image.open(d/f'{n:03}_head_indices.png'));rest=np.array(Image.open(d/f'{n:03}_remaining_fourth_indices.png'));owner=ownership(n)
        layers={0:base,5:head}
        for b in(6,7,8):layers[b]=np.where(owner==b,rest,0).astype(np.uint8)
        full=compose(a,layers,15);need(full.tobytes()==Image.open(d/f'{n:03}_preview.png').convert('RGBA').tobytes(),'Layer split changed full art')
        rm=next(r for r in meta['records']if r['ref']==n)
        choices=sorted(rm['existing_record_candidates'],key=lambda h:(struct.unpack('<BBbb',bytes.fromhex(h))[1],h));need(choices,'No reusable head record')
        chosen=choices[0]
        for b,v in layers.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(owner).save(o/f'{n:03}_ownership.png');full.save(o/f'{n:03}_fourth.png');a.rgba(base).save(o/f'{n:03}_base.png')
        rows.append({'ref':n,'body_source_page':REFS[n],'head_record_hex':chosen,'head_record_existing_not_new':True,'layer_pixels':{str(b):int(np.count_nonzero(v))for b,v in layers.items()},
                     'layer_sha256':{str(b):sha(v.tobytes())for b,v in layers.items()},'base_source_exact':True,'full_target_exact':True})
        pics.extend([(f'{n} base+Head',compose(a,layers,1)),(f'{n} Body+Arm+Leg',compose(a,layers,14)),(f'{n} full',full)])
        if n in(33,39,41,49):page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=3)
    for start in range(0,len(pics),12):page(pics[start:start+12],a.composite(0,15)[0],o/f'ownership_comparison_{start//12:02}.png',cols=3,scale=3)
    write(o/'registration.json',{'candidate_only':True,'source_parent_sha256':sha(P.read_bytes()),'head_probe_sha256':sha((d/'probe.json').read_bytes()),'rows':rows,
          'part_ownership_policy':'새 기본 머리/얼굴 공통. 새 포스 장식=Head, 앞 발사팔=Arm, 망토/다른 소매=Body, 다리/부츠=Leg. 원래 파츠 개념과 동작을 유지.',
          'full_target_exact':True,'source_base_exact':True,'native_bank_boundaries_changed':False,'runtime_verified':False,'all_partial_visual_review_pending':True})
    print(json.dumps({'candidates':len(rows),'head_record_choices':[(r['ref'],r['head_record_hex'])for r in rows]}))
if __name__=='__main__':main()
