"""Validate actual decoded ARC masks and original gun contact, without emulation."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,need,write,helper
from pack_cycle import PLACEHOLDERS
REFS=tuple(range(67,85))+(93,94);PBS=(0,5,6,7,8);DRAW=((8,8),(1,5),(4,7),(2,6))
def main():
 p=argparse.ArgumentParser();p.add_argument('--folder',default='packed_structure_diagnostic_v1');p.add_argument('--targets',default='joint_layers_diagnostic_v2');args=p.parse_args();o=D/args.folder;td=D/args.targets
 a=Archive((D.parent/'air_repaint/packed_air_candidate_v1/PL00_U.ARC').read_bytes());b=Archive((o/'PL00_U.ARC').read_bytes());meta=json.loads((o/'verification.json').read_text('utf8'));need(sha(a.data)==meta['before']and sha(b.data)==meta['after'],'Prepared hash');targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS};checks=unchanged=0
 for n in range(237):
  if n in PLACEHOLDERS:continue
  for mask in range(16):
   for arm in(1,2):
    actual=b.composite(n,mask,arm)[0]
    if n not in REFS:expected=a.composite(n,mask,arm)[0];unchanged+=1
    else:
     expected=b.rgba(targets[n,0])
     for bit,pb in DRAW:
      if mask&bit:expected.alpha_composite(b.rgba(targets[n,pb],32 if pb==7 and arm==2 else 16))
    need(actual.tobytes()==expected.tobytes(),f'RGBA {n}/{mask}/{arm}');checks+=1
  if n%32==0:print(json.dumps({'ref':n,'checked':checks}),flush=True)
 reach=json.loads((D/'fire_constraints/manifest.json').read_text('utf8'));guns=[]
 for n in range(68,85,2):
  q=next(q for q in reach['frames']if q['ref']==n);g=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'));ys,xs=np.nonzero(g);x0=int(xs.min());y0=int(ys.min());y1=int(ys.max()+1)
  for mask in range(16):
   for arm in(1,2):
    old=np.array(a.composite(n,mask,arm)[0]);new=np.array(b.composite(n,mask,arm)[0]);need(np.array_equal(old[y0:y1,x0:x0+8],new[y0:y1,x0:x0+8]),f'Original gun RGBA {n}/{mask}/{arm}');yy,xx=np.nonzero(new[:,:,3]);mx=int(xx.min()-160);my=float(np.median(yy[xx==xx.min()])-160);need(mx==q['muzzle'][0]and abs(my-q['muzzle'][1])<=.5,f'Muzzle {n}/{mask}/{arm}');guns.append([n,mask,arm,mx,my])
 for i,refs in enumerate(((67,68,71,72),(75,76,79,80),(81,82,83,84),(93,94)),1):
  helper.grid([(f'mask {mask:X}',[(f'ref {n}',b.composite(n,mask)[0])for n in refs])for mask in(0,1,2,4,8,15)],o/f'partial_{i}.png',4)
 write(o/'mask_verification.json',{'passed':True,'prepared_sha256':sha(b.data),'rgba_combinations':checks,'nonselected_exact':unchanged,'target_combinations':checks-unchanged,'original_gun_rgba_and_muzzle_checks':len(guns),'gun_details':guns,'runtime_verified':False,'art_approval':False,'scope':'기술 구조 검증. 미완료 71/75 미술 수용과 무관.'});print(json.dumps({'passed':True,'rgba':checks,'guns':len(guns)}))
if __name__=='__main__':main()
