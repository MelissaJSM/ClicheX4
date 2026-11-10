"""Use only the newly drawn rear shin/shoe; protect the rest of both figures."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore'),str(W/'nana_audit/base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();src=D/'rearfoot_edit01/generated.png';assert sha(src)=='97ba28d207b3ac19e7fbce658897d5cc8d9eb879b86c139bd2b946192a8f409e'
a=Archive((W/'root_nana_shot87/packed_settle01/PL00_U.ARC').read_bytes());im=Image.open(src).convert('RGBA');out=D/'rearfoot_registered01';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));Y-=160;X-=160
donors=[]
for i in(0,1):
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[i*16:i*16+16]],np.float32);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop((i*im.width//2,0,(i+1)*im.width//2,im.height)),(96,96),pal,'area_vote');donors.append(z);Image.fromarray(z).save(out/f'donor_{i}.png')
roi=(X>=-8)&(X<=6)&(Y>=12)&(Y<=18);records=[]
for n in(229,230):
 folder=D/('body_layers_probe01'if n==229 else'shoot_layers_probe02');ls={pb:np.array(Image.open(folder/f'layer{pb}_{n}.png'))for pb in(0,5,6,7,8)};oldleg=ls[8].copy();newleg=oldleg.copy();newleg[roi]=donors[0][roi];ls[8]=newleg
 assert np.array_equal(newleg[~roi],oldleg[~roi]);Image.fromarray(newleg).save(out/f'layer8_{n}.png');rows=[]
 for form,mask in [('basic_legs',8),('fourth',15)]:
  old=a.rgba(ls[0]);new=old.copy()
  for bit,pb in((8,8),(1,5),(4,7),(2,6)):
   if mask&bit:old.alpha_composite(a.rgba(oldleg if pb==8 else ls[pb],32 if pb==7 else 16));new.alpha_composite(a.rgba(ls[pb],32 if pb==7 else 16))
  rows.append((f'{form} {n} local rear foot',[('prior new body',old),('new source donor',a.rgba(donors[0 if mask==8 else 1],0 if mask==8 else 16)),('only rear shin/shoe applied',new)]));records.append({'ref':n,'form':form,'changed_layer8_pixels':int((newleg!=oldleg).sum()),'all_pixels_outside_world_roi_exact':True,'roi':[-8,12,7,19],'components8':int(label(np.array(new)[:,:,3]>0,np.ones((3,3)))[1]),'lowest_foot_y_exact':old.getbbox()[3]==new.getbbox()[3],'source_pixel_values_exact':True})
 helper.grid(rows,out/f'comparison_{n}.png',6)
(out/'manifest.json').write_text(json.dumps({'source_sha256':sha(src),'source_size':list(im.size),'direct_native_registration':[96,96],'rows':records,'other_layers_changed':False,'accepted':False,'native_packed':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(records))
