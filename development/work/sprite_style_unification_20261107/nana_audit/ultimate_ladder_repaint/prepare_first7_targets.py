"""허용된5고유몸체와반전2만35층으로 묶는다. 보류7참조는미포함."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
REFS=(143,144,145,146,147,154,183);PBS=(0,5,6,7,8)
HANDS={154:[(-12,6,-7,10)],183:[(-12,2,-7,6),(9,2,15,6)]}
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes());out=D/'first7_targets_v1';out.mkdir(exist_ok=False);hashes={};records=[];rows=[]
 for n in REFS:
  links=[]
  if n in HANDS:
   src=D/'c_common_probe_v2';b=np.array(Image.open(src/f'before_{n:03}_indices.png'));v=np.array(Image.open(src/f'after_{n:03}_indices.png'));oldv=v.copy()
   for x0,y0,x1,y1 in HANDS[n]:
    window=(slice(y0+160,y1+160),slice(x0+160,x1+160));need(not np.isin(b[window],(5,6,7,8,9,15)).any(),'새손 창의 의상색 배제');v[window]=b[window]
   links=[{'world':[int(x-160),int(y-160)],'previous':int(oldv[y,x]),'new_source_index':int(b[y,x])}for y,x in np.argwhere(v!=oldv)]
   ls={0:v,5:np.where((b!=v)|(b==15),b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  else:
   src=D/('a_mirror_probe_v1'if n in (145,147) else 'a_layers_probe_v1');ls={pb:np.array(Image.open(src/f'layer{pb}_{n:03}.png'))for pb in PBS};v=ls[0];b=v.copy();b[ls[5]>0]=ls[5][ls[5]>0]
  need(label(v>0,np.ones((3,3)))[1]==label(b>0,np.ones((3,3)))[1]==1,'한몸체 연결');hashes[str(n)]={}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');hashes[str(n)][str(pb)]=sha(z.tobytes())
  for form,z in(('before',b),('after',v)):Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
  for mask in range(32):
   expected=a.rgba(b,16)if mask&1 else a.rgba(v)
   for arm in (1,2):need(composite(a,ls,mask,arm).tobytes()==expected.tobytes(),'부분RGBA')
  rows.append((str(n),[('old before',a.composite(n,15)[0]),('new before',composite(a,ls,15)),('old after',a.composite(n)[0]),('new after',composite(a,ls,0))]))
  records.append({'ref':n,'source_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'source_manifest_sha256':digest(src/'manifest.json'),'shared_new_hand_boxes':HANDS.get(n,[]),'shared_new_hand_links':links,'target_layer_hashes':hashes[str(n)],'components8':1})
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
 write(out/'manifest.json',{'parent_sha256':digest(parent),'refs':list(REFS),'new_body_refs':[143,144,146,154,183],'new_mirror_refs':[145,147],'remaining_unmodified_refs':[148,149,150,151,152,153,155],'targets':hashes,'frames':records,'direct_rgba_combinations':448,'scope':'허용된 첫3·별개154/183와2반전만 묶은 미술후보. 보류149151153 및그연동148150152155 미수정. 양폼반전은 기존재킷 좌표를 새공통몸체에 적용한새정책이며 원후폼exact복원이아님.','native_packed':False,'runtime_verified':False});print(json.dumps({'layers':35,'rgba':448,'new_hand_cells':{q['ref']:len(q['shared_new_hand_links'])for q in records},'sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
