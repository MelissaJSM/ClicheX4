from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import sha,write
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from prepare import FACE
PBS=(0,5,6,7,8);refs=(68,70,72,74,76,78,80,84)
a=Archive((H/'PL02_U.ARC').read_bytes());b=Archive((H/'PL02_fixed.ARC').read_bytes());same=changed=0;rows=[]
gd=ROOT/'work/sprite_style_unification_20261107/shibuki_audit/ultimate_dash_barrel_guard01';meta=json.loads((gd/'report.json').read_text('utf8'))['rows']
for n in range(237):
 if n in {105,*range(175,183)}:continue
 for pb in PBS:
  old=a.layer(n,pb)[0];new=b.layer(n,pb)[0]
  if n not in refs:assert np.array_equal(old,new),(n,pb);same+=1
  else:
   assert np.array_equal(new,np.array(Image.open(H/f'candidate/layer{pb}_{n:03}.png')))
   q=72 if n==74 else n;guard=np.array(Image.open(gd/f'{q:03}_mask.png'))>0
   allowed=np.array(Image.open(H/f'candidate/mask_{n:03}.png'))>0
   assert np.array_equal(old[guard],new[guard])
   assert np.array_equal(old[~allowed],new[~allowed])
   x0,y0,x1,y1=[v+160 for v in FACE[n]]
   assert np.array_equal(old[y0:y1,x0:x1],new[y0:y1,x0:x1]),('Face changed',n,pb)
   changed+=int(np.any(old!=new))
 for form,mask in [('before',15),('after',0)]:
  old=np.array(a.composite(n,mask)[0]);new=np.array(b.composite(n,mask)[0]);actual_changed=bool(np.any(new!=old))
  if n in refs:
   q=72 if n==74 else n;r=next(r for r in meta if r['shot_ref']==q);mx,my=r['muzzle_world']
   connected,count=label(new[:,:,3]>0,np.ones((3,3)))
   sizes=sorted((int((connected==k).sum()) for k in range(1,count+1)),reverse=True)
   oldlab,oldcount=label(old[:,:,3]>0,np.ones((3,3)));old_sizes=sorted((int((oldlab==k).sum()) for k in range(1,oldcount+1)),reverse=True)
   assert sum(s>=12 for s in sizes)<=sum(s>=12 for s in old_sizes),'New detached part'
   adjacent=new[160+my-1:160+my+2,160+mx+10,3]>0
   rows.append({'ref':n,'form':form,'changed':actual_changed,'rear_center_contact_rows':int(adjacent.sum()),'components8':sizes,'before_components8':old_sizes})
  else:assert not actual_changed,(n,form)
assert a.p==b.p and len(a.data)==len(b.data)
write(H/'validation.json',{'passed':True,'untouched_layers_equal':same,'changed_layers':changed,'target_frames':list(refs),'rows':rows,'palette_exact':True,'native_weapon_guards_exact':40,'face_rectangles_exact':40,'outside_arm_registration_equal':True,'accepted_idle_and_other_motion_equal':True,'parent_sha256':sha(a.data),'output_sha256':sha(b.data)})
print('checked',same,'untouched layers;',changed,'changed layers; rear contact',[(r['ref'],r['form'],r['rear_center_contact_rows']) for r in rows])
