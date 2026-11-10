"""실제 wall ARC의 모든 부분파츠/팔종류와 총구/접점을 검증한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,need,write,helper
from pack_cycle import PLACEHOLDERS
PBS=(0,5,6,7,8);DRAW=((8,8),(1,5),(4,7),(2,6))
def main():
    p=argparse.ArgumentParser();p.add_argument('--folder',default='packed_wall_candidate_v2');p.add_argument('--targets',default='joint_layers_probe_v2');args=p.parse_args();out=D/args.folder;td=D/args.targets
    a=Archive((D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC').read_bytes());b=Archive((out/'PL00_U.ARC').read_bytes());meta=json.loads((out/'verification.json').read_text('utf8'));need(sha(a.data)==meta['before']and sha(b.data)==meta['after'],'Prepared hash');targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in range(55,67)for pb in PBS};checks=unchanged=0
    for n in range(237):
        if n in PLACEHOLDERS:continue
        for mask in range(16):
            for arm in(1,2):
                actual=b.composite(n,mask,arm)[0]
                if n not in range(55,67):expected=a.composite(n,mask,arm)[0];unchanged+=1
                else:
                    expected=b.rgba(targets[n,0])
                    for bit,pb in DRAW:
                        if mask&bit:expected.alpha_composite(b.rgba(targets[n,pb],32 if pb==7 and arm==2 else 16))
                need(actual.tobytes()==expected.tobytes(),f'RGBA {n}/{mask}/{arm}');checks+=1
        if n%32==0:print(json.dumps({'ref':n,'checked':checks}),flush=True)
    plan=json.loads((D/'inputs.json').read_text('utf8'));reach=json.loads((D/'shot_reach_review_v4/reach.json').read_text('utf8'));contacts=[]
    for n in range(55,67,2):
        old=a.layer(n)[0];new=b.layer(n)[0];f=n+1;q=next(q for q in reach['frames']if q['ref']==f);ex,ey=map(int,next(q['eye_world']for q in plan['frames']if q['ref']==n));need(new[ey+160,ex+160]==14,'Eye drift');fy=int(np.nonzero(new)[0].max()-160);need(fy==int(np.nonzero(old)[0].max()-160),'Floor y')
        muzzle_checks=[]
        for mask in range(16):
            for arm in(1,2):
                rgba=np.array(b.composite(f,mask,arm)[0]);y,x=np.nonzero(rgba[:,:,3]);mx=int(x.min()-160);my=float(np.median(y[x==x.min()])-160);need(mx==q['old_muzzle'][0],f'Muzzle x {f}/{mask}/{arm}');need(abs(my-q['old_muzzle'][1])<=.5,f'Muzzle y {f}/{mask}/{arm}');muzzle_checks.append([mask,arm,mx,my])
        contacts.append({'ref':n,'eye':[ex,ey],'floor_y':fy,'floor_x':(np.flatnonzero(new[160+fy])-160).tolist(),'shot':f,'muzzle_32_combinations':muzzle_checks})
    for gi,refs in enumerate(((55,56,57,58),(59,60,61,62),(63,64,65,66)),1):
        helper.grid([(f'mask {mask:X}',[(f'ref {n}',b.composite(n,mask)[0])for n in refs])for mask in range(16)],out/f'partial_{gi}.png',4)
    for gi,refs in enumerate(((55,56,57,58,59,60),(61,62,63,64,65,66)),1):
        helper.grid([(f'ref {n}',[(f'mask {m:X}',b.composite(n,m)[0])for m in(0,1,2,4,8,15)])for n in refs],out/f'owner_detail_{gi}.png',4)
    write(out/'mask_verification.json',{'passed':True,'prepared_sha256':sha(b.data),'rgba_combinations':checks,'nonselected_exact':unchanged,'target_combinations':checks-unchanged,'muzzle_checks':192,'contacts':contacts,'arm1_arm2_palette_equal':bool(np.array_equal(b.words[16:32],b.words[32:48])),'runtime_verified':False});print(json.dumps({'passed':True,'checks':checks,'nonselected':unchanged}))
if __name__=='__main__':main()
