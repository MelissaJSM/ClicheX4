"""새 승리4의 양 의상을 기존 Ultimate 의미층에 분리한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PBS=(0,5,6,7,8);REFS=(204,205,206,207)
def composite(a,layers,mask,arm):
 image=a.rgba(layers[0])
 for pb,bit in ((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:image.alpha_composite(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16))
 return image
def main():
 p=N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());src=D/'canonical_weapon_probe_v1';out=D/'final_targets_v1';out.mkdir(exist_ok=False);targets={};frames=[];rows=[]
 for n in REFS:
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));af=np.array(Image.open(src/f'after_{n:03}_indices.png'));need(not((af>0)&(b==0)).any(),'후폼 알파 포함');base=af.copy();overlay=np.where((b!=af)|(b==15),b,0).astype(np.uint8)
  layers={0:base,5:overlay,6:np.zeros_like(base),7:np.zeros_like(base),8:np.zeros_like(base)};targets[str(n)]={}
  for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');targets[str(n)][str(pb)]=sha(z.tobytes())
  zz=base.copy();zz[overlay>0]=overlay[overlay>0];need(np.array_equal(zz,b),'재킷 exact');need(np.array_equal(base,af),'후폼 exact');frames.append({'ref':n,'before_source':(src/f'before_{n:03}_indices.png').relative_to(ROOT).as_posix(),'after_source':(src/f'after_{n:03}_indices.png').relative_to(ROOT).as_posix(),'before_sha256':sha(b.tobytes()),'after_sha256':sha(af.tobytes()),'layer5_pixels':int((overlay>0).sum()),'after_outside_before':0})
  rows.append((str(n),[('old before',a.composite(n,15)[0]),('new before',a.rgba(b,16)),('old after',a.composite(n)[0]),('new after',a.rgba(af))]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'manifest.json',{'parent_arc_sha256':digest(p),'source_manifest_sha256':digest(src/'manifest.json'),'refs':list(REFS),'targets':targets,'frames':frames,'scope':'새 승리4몸체×2의상→20층. 기존과 동일한 Ultimate base0/재킷5 정책,6/7/8 빈층. 별도 효과 없음.','runtime_verified':False})
if __name__=='__main__':main()
