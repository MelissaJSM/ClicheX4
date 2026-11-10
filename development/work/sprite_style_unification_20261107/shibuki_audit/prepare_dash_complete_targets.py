"""대시10몸체+8사격+원속도선2의100층을 조립 전 목표로 고정한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from prepare_dash_body_layers import P
REFS=(67,69,71,75,77,79,81,83,93,94)
SHOTS={68:'dash_shot_page01_final01',70:'dash_shot_page01_final01',72:'dash_shot_page02_final01',76:'dash_shot_page02_final01',78:'dash_shot_page03_final01',80:'dash_shot_page03_final01',82:'dash82_arm_native04',84:'dash_shot_page04_final01'}
def main():
    o=H/'dash_complete_targets01';need(not o.exists(),'Fresh targets required');o.mkdir();a=Archive(P.read_bytes());targets={n:{b:np.array(Image.open(H/f'dash_body_layers01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}for n in REFS};sources={};proof=[]
    for n,folder in SHOTS.items():
        d=H/folder;body=targets[n-1];layers={0:np.array(Image.open(d/f'base_{n:03}_indices.png'))};allowed=np.array(Image.open(d/f'fourth_{n:03}_allowed_mask.png'))>0;ring=np.array(Image.open(d/f'fourth_{n:03}_gun_ring_clear_mask.png'))>0;guard=np.array(Image.open(H/f'dash_barrel_guard02/{n:03}_mask.png'))>0;source=np.array(Image.open(d/f'fourth_{n:03}_registered_arm_indices.png'))
        for b in(5,6,7,8):
            ar=body[b].copy();ar[allowed]=0
            if b==7:ar[allowed&~guard&~ring]=source[allowed&~guard&~ring]
            ar[guard]=0;layers[b]=ar
        need(compose(a,layers,15).tobytes()==Image.open(d/f'fourth_{n:03}.png').convert('RGBA').tobytes(),'Full split mismatch');need(a.rgba(layers[0]).tobytes()==Image.open(d/f'base_{n:03}.png').convert('RGBA').tobytes(),'Base split mismatch');targets[n]=layers
        for arm in(1,2):
            for mask in range(16):need(np.array_equal(np.array(compose(a,layers,mask,arm))[guard],np.array(a.rgba(layers[0]))[guard]),'Partial changes canonical gun')
        sources[folder+'/report.json']=sha((d/'report.json').read_bytes())
    for n,bn in ((73,71),(74,72)):
        layers={b:v.copy()for b,v in targets[bn].items()};streak=np.array(Image.open(H/f'dash_speed_streak_audit02/{n:03}_original_streak_indices.png'));layers[0][streak>0]=streak[streak>0];targets[n]=layers
        proof.append({'ref':n,'body':bn,'original_streak_pixels':int((streak>0).sum()),'original_streak_raw_sha256':sha(streak.tobytes()),'order':'새몸체 이후 원래9속도선, 그 뒤 장비층. 원래74의 이전 X 몸체겹침1px는 새몸에 옮기지 않음.'})
    rows=[];files={}
    for n,ll in sorted(targets.items()):
        for b,ar in ll.items():
            f=o/f'{n:03}_bank{b}_indices.png';Image.fromarray(ar).save(f);files[f.name]=sha(f.read_bytes())
        compose(a,ll,0).save(o/f'base_{n:03}.png');compose(a,ll,15).save(o/f'fourth_{n:03}.png')
        page([(f'{n} mask{m:X}',compose(a,ll,m))for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=3)
        rows.append({'ref':n,'pixels':{str(b):int((ar>0).sum())for b,ar in ll.items()},'source_shot_folder':SHOTS.get(n),'source_body':n if n in REFS else n-1 if n in SHOTS else n-2})
    for form,mask in(('base',0),('fourth',15)):
        items=[(f'{form} {n}',compose(a,ll,mask))for n,ll in sorted(targets.items())]
        for i in range(0,len(items),6):page(items[i:i+6],a.composite(0,mask)[0],o/f'{form}_all_{i//6:02}.png',cols=3,scale=4)
    write(o/'targets.json',{'parent_sha256':sha(P.read_bytes()),'rows':rows,'source_reports':sources,'streak_proof':proof,'partial_combinations':len(rows)*32,'shot_guards':len(SHOTS)*32,'bank_boundaries_must_preserve':True,'palette_must_preserve':True,'native_cpu_verified':False,'gameplay_verified':False});write(o/'LOCK.json',{'parent_sha256':sha(P.read_bytes()),'target_manifest_sha256':sha((o/'targets.json').read_bytes()),'files':files,'source_reports':sources});print(json.dumps({'refs':len(rows),'layers':len(files),'output':str(o),'lock_sha256':sha((o/'LOCK.json').read_bytes())}))
if __name__=='__main__':main()
