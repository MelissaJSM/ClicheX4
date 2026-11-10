"""새 이동/사격을 공통 머리·의상 소유 층으로 구성한다. 게임 파일 쓰기 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
PARTS=(0,5,6,7,8)
PARENT='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--moving-only',action='store_true');ap.add_argument('--standing',default='base_run_standing02_registered03');z=ap.parse_args()
    out=(H/z.output).resolve();need(out.is_relative_to(H.resolve()) and not out.exists(),'Fresh isolated output required')
    data=(H/'prepared_dash_base01/PL00_U.ARC').read_bytes();need(sha(data)==PARENT,'Wrong parent');a=Archive(data);out.mkdir();rows=[];source_files={};targets={};review=[]
    folders={n:f'base_run_shot_page{(n-4)//6+1:02}_registered02' for n in range(4,33,2)}
    if not z.moving_only:folders[2]=z.standing
    refs=range(3,33) if z.moving_only else range(1,33)
    def read(rel):
        p=H/rel;source_files[rel]=sha(p.read_bytes());return np.array(Image.open(p))
    for n in refs:
        if n==1:layers={b:a.layer(0,b)[0].copy() for b in PARTS};source='accepted idle0';kind='exact_idle0_reuse'
        elif n%2:
            layers={b:read(f'base_run_body_layers02/{n:03}_bank{b}_indices.png') for b in PARTS};source='base_run_body_layers02';kind='new_body'
        else:
            folder=folders[n];d=H/folder;report=json.loads((d/'report.json').read_text('utf8'));need(report['alpha_registration_passed'],'Unresolved source alpha '+folder);source_files[folder+'/report.json']=sha((d/'report.json').read_bytes())
            body={b:a.layer(0,b)[0].copy() for b in PARTS} if n==2 else targets[n-1]
            layers={0:read(f'{folder}/base_{n:03}_indices.png')}
            allowed=read(f'{folder}/fourth_{n:03}_allowed_mask.png')>0
            arm=read(f'{folder}/fourth_{n:03}_registered_arm_indices.png')
            guard=read(f'base_run_shot_inputs01/barrels/{n:03}_mask.png')>0
            gun=read(f'base_run_shot_inputs01/barrels/{n:03}_indices.png')
            for b in PARTS[1:]:
                ar=body[b].copy();ar[allowed]=0
                if b==7:ar[allowed&~guard]=arm[allowed&~guard]
                ar[guard]=0;layers[b]=ar
            want=read(f'{folder}/fourth_{n:03}.png');need(np.array_equal(np.array(compose(a,layers,15)),want),'Full shot layer mismatch '+str(n))
            need(np.array_equal(np.array(a.rgba(layers[0])),read(f'{folder}/base_{n:03}.png')),'Base shot mismatch')
            for mask in range(16):
                for armtype in (1,2):need(np.array_equal(np.array(compose(a,layers,mask,armtype))[guard],np.array(a.rgba(gun))[guard]),'Partial changes original gun')
            source=folder;kind='new_arm_on_accepted_body' if n==2 else 'new_arm_on_new_body'
        targets[n]=layers
        full=compose(a,layers,15);base=a.rgba(layers[0])
        if n%2 and n!=1:
            need(full.tobytes()==Image.open(H/f'base_run_common01/fourth_{n:03}.png').convert('RGBA').tobytes(),'Body ownership changes full')
        if n==1:
            for mask in range(16):
                for armtype in (1,2):need(compose(a,layers,mask,armtype).tobytes()==a.composite(0,mask,armtype)[0].tobytes(),'Entry1 differs from accepted0')
        for b,ar in layers.items():Image.fromarray(ar).save(out/f'{n:03}_bank{b}_indices.png')
        base.save(out/f'base_{n:03}.png');full.save(out/f'fourth_{n:03}.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],out/f'partial_{n:03}.png',cols=4,scale=3)
        review.extend([(f'{n} base',base),(f'{n} arm only',compose(a,layers,4)),(f'{n} full',full)])
        rows.append({'ref':n,'kind':kind,'source':source,'body_ref':0 if n<=2 else (n if n%2 else n-1),'layer_pixels':{str(b):int((v>0).sum())for b,v in layers.items()},'layer_raw_sha256':{str(b):sha(v.tobytes())for b,v in layers.items()}})
    for i in range(0,len(review),12):page(review[i:i+12],a.composite(0,15)[0],out/f'ownership_{i//12:02}.png',cols=3,scale=4)
    write(out/'targets.json',{'candidate_only':True,'parent_sha256':PARENT,'rows':rows,'source_files':source_files,'partial_cases':len(rows)*32,'gun_cases':len(folders)*32,'idle0_141_142_not_targets':True,'native_cpu_verified':False,'arc_written':False})
    files={p.name:sha(p.read_bytes())for p in sorted(out.glob('*_indices.png'))}
    write(out/'LOCK.json',{'target_manifest_sha256':sha((out/'targets.json').read_bytes()),'files':files,'source_files':source_files,'runtime_verified':False})
    print(json.dumps({'refs':len(rows),'layer_targets':len(files),'partial_cases':len(rows)*32,'lock':sha((out/'LOCK.json').read_bytes())}))

if __name__=='__main__':main()
