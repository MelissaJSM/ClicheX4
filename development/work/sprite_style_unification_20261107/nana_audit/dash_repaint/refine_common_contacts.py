"""Fix a split-leg row and preserve authored boot contacts in the common candidate."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore'),str(D.parent/'air_repaint')]
from preview_restore import Archive,write,sha,need,helper
from prepare_air_joint_layers import quantize_rgba_row,spans
sys.path.insert(0,str(D))
from prepare_next_guides import body_path
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());o=D/'common_contact_refine_v1';need(not o.exists(),'Fresh');o.mkdir();rows=[];proof=[]
 for n in(79,93):
  before=np.array(Image.open(D/'common_silhouette_probe_v4'/f'base_{n:03}.png'));src=np.array(Image.open(body_path(n)));new=before.copy();f=np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png'));links=[]
  if n==93:
   # The y9 skin/boot row has TWO Fourth spans. The earlier nearest-span
   # selection wrongly collapsed both authored limbs into the small rear one.
   # Retain exact new-art texels wherever the agreed silhouette contains them.
   for y in range(9,12):
    mask=f[160+y]>0;new[160+y]=0;new[160+y,mask]=src[160+y,mask]
    links.append({'world_y':y,'exact_authored_texels':(np.where(mask&(src[160+y]>0))[0]-160).tolist()})
  else:
   # Keep the actual new boot sole dimensions. Only the Fourth shoe in the
   # same three rows is sampled across that contact, never the bare calf.
   rgba=Image.open(D/'fourth_contacts_probe_v2/source_rgba8_079.png').convert('RGBA');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float)
   for y in range(20,23):
    bx=np.where(src[160+y]>0)[0];fx=np.where(f[160+y]>0)[0];need(len(bx)>0 and len(fx)>0,'Sole');new[160+y]=src[160+y];box=((int(fx.min())-120)*8,(y+40)*8,(int(fx.max())+1-120)*8,(y+41)*8);v,cov=quantize_rgba_row(rgba.crop(box),len(bx),pal);f[160+y]=0;f[160+y,bx]=v;links.append({'world_y':y,'original_new_boot_exact':True,'fourth_shoe_rgba_box':box,'width_before':len(fx),'width_after':len(bx)})
  Image.fromarray(new).save(o/f'base_{n:03}.png');Image.fromarray(f).save(o/f'fourth_{n:03}.png');full=np.where(f,f,new).astype(np.uint8);rows.append((f'{n} 국소 접점',[('새 기본 원화',a.rgba(src)),('이전 공통',a.rgba(before)),('국소 수정',a.rgba(new)),('포스',a.rgba(full,16))]));proof.append({'ref':n,'before':sha(before.tobytes()),'after':sha(new.tobytes()),'links':links})
 helper.grid(rows,o/'comparison.png',8);write(o/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':proof,'native_packed':False,'runtime_verified':False})
if __name__=='__main__':main()
