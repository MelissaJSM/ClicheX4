from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,helper,sha
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());out=D/'geometry_position_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for n in(95,98):
  for form,start,mask in(('before',16,15),('after',0,0)):
   z=np.array(Image.open(D/f'geometry_registered_v1/{form}_{n:03}_indices.png'));dx,dy=(0,-3)if n==95 else(1,0);v=np.roll(np.roll(z,dy,0),dx,1);Image.fromarray(v).save(out/f'{form}_{n:03}_indices.png')
   rows.append((f'{form} {n}',[('idle',a.composite(0,mask)[0]),('old fixed',a.composite(n,mask)[0]),('new geometry fixed',a.rgba(z,start)),('translation probe',a.rgba(v,start))]));records.append({'ref':n,'form':form,'translation':[dx,dy],'source_sha256':sha(z.tobytes()),'target_sha256':sha(v.tobytes()),'candidate_only':True})
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'manifest.json',{'scope':'새 국소 원화의 전신 강체이동 진단. 머리/손발 최종 채택 아님.','records':records,'native_packed':False});print(out)
if __name__=='__main__':main()
