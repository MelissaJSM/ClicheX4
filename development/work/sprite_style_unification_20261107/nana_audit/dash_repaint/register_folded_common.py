"""Register authored folded knee material without combining the two legs."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore'),str(D.parent/'air_repaint')]
from preview_restore import Archive,sha,need,write,helper
from prepare_air_joint_layers import quantize_rgba_row
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());o=D/'folded_common_probe_v1';need(not o.exists(),'Fresh');o.mkdir();rows=[];proof=[];Y,X=np.indices((384,384));x=X-160;y=Y-160;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float)
 for n in(71,75):
  b=np.array(Image.open(body_path(n)));original=np.array(Image.open(D/'folded_leg_composite_v3'/f'fourth_{n:03}.png'));f=original.copy();field=Image.open(D/'folded_leg_composite_v3'/f'rear_source_rgba8_{n:03}.png').convert('RGBA');links=[]
  for yy in range(17,21):
   dest=np.where(np.isin(b[yy+160],[10,11,12])&(x[0]<=-3))[0];src=np.where(np.isin(original[yy+160],[10,11,12])&(x[0]<=-3))[0]
   if not len(dest)or not len(src)or np.all(f[yy+160,dest]>0):continue
   box=((int(src.min())-120)*8,(yy+40)*8,(int(src.max())+1-120)*8,(yy+41)*8);vals,cov=quantize_rgba_row(field.crop(box),len(dest),pal);f[yy+160,dest]=vals;links.append({'world_y':yy,'source_rgba_box':box,'destination_world':(dest-160).tolist(),'source_colors':vals.tolist(),'coverage':cov})
  new=b.copy();removed=(b>0)&(f==0)&(y>=16);new[removed]=0
  need(label(new>0,np.ones((3,3)))[1]==1,'Base connected');need(label(f>0,np.ones((3,3)))[1]==1,'Fourth connected');need(np.array_equal(new[:176],b[:176]),'Base upper exact')
  for key,z in(('base',new),('fourth',f)):Image.fromarray(z).save(o/f'{key}_{n:03}.png')
  rows.append((f'{n} 공통 접점',[('새 기본',a.rgba(b)),('기본 외곽 접점',a.rgba(new)),('포스 수용 원화',a.rgba(original,16)),('같은 원화 무릎 정합',a.rgba(f,16))]));proof.append({'ref':n,'base_before':sha(b.tobytes()),'base_after':sha(new.tobytes()),'fourth_before':sha(original.tobytes()),'fourth_after':sha(f.tobytes()),'same_pose_knee_source_links':links,'base_outline_removed':[(int(xx-160),int(yy-160),int(b[yy,xx]))for yy,xx in np.argwhere(removed)],'foot_floor_y':int(np.nonzero(new)[0].max()-160),'foot_floor_x':(np.flatnonzero(new[np.nonzero(new)[0].max()])-160).tolist()})
 helper.grid(rows,o/'comparison.png',8);write(o/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False});print(json.dumps(proof))
if __name__=='__main__':main()
