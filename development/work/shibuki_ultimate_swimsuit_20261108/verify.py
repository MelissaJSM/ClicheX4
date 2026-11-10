from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import board,write,sha
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
a=Archive((H/'PL02_U.ARC').read_bytes());b=Archive((H/'PL02_fixed.ARC').read_bytes());meta=json.loads((H/'expanded/registration.json').read_text('utf8'));refs=meta['refs'];same=changed=0;garment_pixels=0;rows=[]
for n in range(237):
 if n in (105,*range(175,183)):continue
 mask=np.array(Image.open(H/f'expanded/mask_{n:03}.png'))>0 if n in refs else np.zeros((384,384),bool)
 for pb in (0,5,6,7,8):
  old=a.layer(n,pb)[0];new=b.layer(n,pb)[0]
  assert np.array_equal(old[~mask],new[~mask]),('Outside clothing',n,pb)
  if n in refs:assert np.array_equal(new,np.array(Image.open(H/f'expanded/layer{pb}_{n:03}.png'))),(n,pb)
  if np.array_equal(old,new):same+=1
  else:changed+=1;garment_pixels+=int((old!=new).sum())
  if pb!=0 and not 217<=n<=230:assert np.array_equal(old,new),('Jacket changed',n,pb)
 for form,m in [('before',15),('after',15 if 217<=n<=230 else 0)]:
  old=np.array(a.composite(n,m)[0]);new=np.array(b.composite(n,m)[0]);assert np.array_equal(old[~mask],new[~mask]),(n,form)
  if n in refs:rows.append({'ref':n,'form':form,'changed_pixels':int(np.any(old!=new,axis=2).sum()),'outside_clothing_exact':True})
assert a.p==b.p and len(a.data)==len(b.data)
for n in (0,115,116,117,118,119,68,70,72,74,76,78,80,84):
 for pb in (0,5,6,7,8):assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0]),('Accepted idle/wrist changed',n,pb)
for i in range(0,len(refs),24):
 ns=refs[i:i+24];board([(str(n),b.composite(n,15 if 217<=n<=230 else 0)[0]) for n in ns],H/f'packed_{i//24:02}.png',cols=6)
for name,ns in {'fire':[0,85,86,87,0,88,89,90,91,92,0],'special':[0,97,98,99,100,101,102,103,104,231,232,0],'hover':[0,221,222,223,224,225,226,227,228,229,230,0]}.items():
 frames=[]
 for n in ns:
  im=Image.new('RGB',(384,320),(28,36,49));s=b.composite(n,15 if 217<=n<=230 else 0)[0].crop((112,120,208,200)).resize((384,320),Image.Resampling.NEAREST);im.paste(s,(0,0),s);frames.append(im)
 frames[0].save(H/f'{name}.gif',save_all=True,append_images=frames[1:],duration=180,loop=0)
write(H/'validation.json',{'passed':True,'changed_refs':refs,'changed_layers':changed,'identical_layers':same,'changed_indexed_pixels':garment_pixels,'outside_garment_equal':True,'idle_and_wrist_v3_exact':True,'jacket_layers_exact_except_ultimate_only_hover_nova':True,'palette_exact':True,'rows':rows,'arc_sha256':sha(b.data),'parent_arc_sha256':sha(a.data)})
print('PASS refs',len(refs),'changed layers',changed,'identical layers',same,'changed pixels',garment_pixels)
