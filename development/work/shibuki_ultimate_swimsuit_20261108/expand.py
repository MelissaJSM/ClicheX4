"""공유 의상 패치를 관련 자세에 정합하고 원래 앞쪽 손/효과를 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(H),str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from register import REGIONS,PBS,mask_for
from common import board,write,sha
from scripts.export_x_consistency import Archive
from pack_local import pack
RELATED={89:[88],95:[96],98:[99],101:[102],106:[107,108],110:[111,233,234,235,236],120:[121,122,123],124:[125],133:[134],135:[136],138:[139],156:[157,158],162:[163,164,165],166:[167,168,169],170:[171,172,173,174],213:[214],215:[216],217:[218,220],221:[222],223:[224],225:[226],227:[228],229:[230],231:[232]}
RELATED[110]=[111];RELATED[234]=[235,236]
def display(a,n):
 v=a.layer(n)[0].copy();owner=np.zeros(v.shape,np.uint8)
 if 217<=n<=230:
  for pb in (8,5,7,6):
   w=a.layer(n,pb)[0];m=w>0;v[m]=w[m];owner[m]=pb
 return v,owner
def main(packed=False):
 a=Archive((H/'PL02_U.ARC').read_bytes());out=H/'expanded';out.mkdir(exist_ok=True);results={};masks={};rows=[];targets={}
 for n in REGIONS:
  results[n]=np.array(Image.open(H/f'candidate/body_{n:03}.png'));masks[n]=np.array(Image.open(H/f'candidate/mask_{n:03}.png'))>0
 for source,refs in RELATED.items():
  orig,_=display(a,source);mask=masks[source];new=results[source];region=mask_for(source);anchor=region&(orig>0);bestrows=[]
  for n in refs:
   if n in REGIONS:continue
   old,_=display(a,n);best=None
   shifts=[(-1,0)] if n==88 else [(dx,dy) for dx in range(-3,4) for dy in range(-3,4)]
   for dx,dy in shifts:
    baseline=np.roll(orig,(dy,dx),(0,1));m=np.roll(anchor,(dy,dx),(0,1));score=int(((baseline==old)&m).sum())-.15*(abs(dx)+abs(dy))
    if best is None or score>best[0]:best=(score,dx,dy,baseline,m)
   score,dx,dy,baseline,anchor2=best;ratio=float(((baseline==old)&anchor2).sum()/anchor2.sum())
   shifted=np.roll(new,(dy,dx),(0,1));m=np.roll(mask,(dy,dx),(0,1))
   # Shared torso texels only: a hand, gun or effect in front stays as authored.
   m&=old==baseline
   result=old.copy();result[m]=shifted[m];results[n]=result;masks[n]=m
   rows.append({'ref':n,'source':source,'translation':[dx,dy],'matching_torso_fraction':round(ratio,4),'changed_pixels':int((result!=old).sum()),'requires_review':ratio<.65})
 for n,new in sorted(results.items()):
  old,owner=display(a,n);changed=old!=new
  for pb in PBS:
   layer=a.layer(n,pb)[0].copy();m=changed&(owner==pb);layer[m]=new[m]
   # Other layers retained exactly, including the capsule-before jacket.
   if m.any():targets[n,pb]=layer
   Image.fromarray(layer).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(changed.astype('uint8')*255).save(out/f'mask_{n:03}.png')
  Image.fromarray(new).save(out/f'body_{n:03}.png')
 pics=[(f'{n} result',a.rgba(new)) for n,new in sorted(results.items())]
 for i in range(0,len(pics),24):board(pics[i:i+24],out/f'sheet_{i//24:02}.png',cols=6)
 write(out/'registration.json',{'refs':sorted(results),'related':rows,'changed_layers':len(targets)})
 if packed:
  data,proof=pack(a.data,targets,PBS,preserve_tiles=True);(H/'PL02_fixed.ARC').write_bytes(data);write(H/'pack.json',proof)
 print('refs',len(results),'layers',len(targets),'related needing visual review',[(r['ref'],r['source'],r['matching_torso_fraction']) for r in rows if r['requires_review']])
if __name__=='__main__':main('--pack' in sys.argv)
