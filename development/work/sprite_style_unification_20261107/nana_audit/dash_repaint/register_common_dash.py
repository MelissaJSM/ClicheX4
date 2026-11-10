"""공동 알파 대안: 원화 발을 변형하지 않고 기본 부츠의 동일 행 명암을 국소 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore'),str(D.parent/'air_repaint')]
from preview_restore import Archive,sha,need,write,helper
from prepare_air_joint_layers import spans,quantize_rgba_row
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
START={67:10,69:13,77:12,79:12,81:7,83:8,93:9,94:3}
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'common_silhouette_probe_v4';need(not out.exists(),'Fresh output');out.mkdir();rows=[];reports=[];pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],float)
 for n,start in START.items():
  b=np.array(Image.open(body_path(n)));f=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png'));new=b.copy();links=[];miss=[];field=body_path(n).parent/f'source_rgba8_{n:03}.png';rgba=Image.open(field).convert('RGBA')if field.exists()and n!=77 else None
  for y in range(160+start,200):
   bs=spans(b[y]>0);fs=spans(f[y]>0)
   for src in bs:
    near=[v for v in fs if max(int(src[0]-v[-1]),int(v[0]-src[-1]),0)<=3]
    if not near:miss.append([int(y-160),int(src[0]-160),int(src[-1]-160)]);continue
    dest=min(near,key=lambda v:abs(float(src.mean()-v.mean())))
    # Preserve the original calf's neighbourhood and exclude unrelated folds.
    dest=dest[(dest>=src[0]-2)&(dest<=src[-1]+2)]
    if not len(dest):miss.append([int(y-160),int(src[0]-160),int(src[-1]-160)]);continue
    ix=np.rint((dest-dest[0])*(len(src)-1)/max(1,int(dest[-1]-dest[0]))).astype(int);new[y,src]=0
    if rgba is not None:
     box=((int(src[0])-120)*8,(y-120)*8,(int(src[-1])+1-120)*8,(y+1-120)*8);vals,cov=quantize_rgba_row(rgba.crop(box),int(dest[-1]-dest[0]+1),pal);new[y,dest]=vals[dest-dest[0]];links.append({'target':[int(dest[0]-160),y-160,int(dest[-1]-160)],'rgba_box':box,'coverage':cov})
    else:
     new[y,dest]=b[y,src[ix]];links.extend([[int(x-160),y-160,int(sx-160),int(b[y,sx])]for x,sx in zip(dest,src[ix])])
  Image.fromarray(new).save(out/f'base_{n:03}.png');full=np.where(f,f,new).astype(np.uint8);Image.fromarray(full).save(out/f'fourth_{n:03}.png');floor=np.nonzero(b)[0].max();reports.append({'ref':n,'base_source_sha256':sha(b.tobytes()),'after':sha(new.tobytes()),'same_row_links':links,'unresolved_rows_preserved':miss,'floor_y_before':int(floor-160),'floor_y_after':int(np.nonzero(new)[0].max()-160),'floor_x_before':(np.flatnonzero(b[floor])-160).tolist(),'floor_x_after':(np.flatnonzero(new[floor])-160).tolist(),'components_8':int(label(new>0,np.ones((3,3)))[1])});rows.append((f'common {n}',[('새 기본',a.rgba(b)),('같은 원화 공동 외곽',a.rgba(new)),('포스 원화 보존',a.rgba(full,16))]))
 for k in range(0,len(rows),3):helper.grid(rows[k:k+3],out/f'comparison_{k//3+1}.png',7)
 write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':reports,'native_packed':False,'runtime_verified':False});print(json.dumps({r['ref']:r['unresolved_rows_preserved']for r in reports}))
if __name__=='__main__':main()
