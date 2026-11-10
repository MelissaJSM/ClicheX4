"""Preserve native return-aura colors and source art while splitting costume layers."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation,distance_transform_edt
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();Y,X=np.indices((384,384));Y-=160;X-=160
PBS=(0,5,6,7,8);ENERGY=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8)
def shift(z,dy):
 assert not z[:abs(dy)].any()and not z[-abs(dy):].any();return np.roll(z,dy,axis=0)
def aura(z):
 m=z>0;return np.where(m,z,np.where(binary_dilation(m),13,np.where(binary_dilation(m,iterations=2),7,0))).astype(np.uint8)
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 parent=W/'root_nana_victory/packed_victory02/PL00_U.ARC';a=Archive(parent.read_bytes());assert sha(a.data)=='90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239'
 out=D/'joint_targets03';out.mkdir(exist_ok=False);reg=D/'registered01'
 b=np.array(Image.open(reg/'base_156_indices.png'));f=np.array(Image.open(reg/'fourth_156_indices.png'));f_before=f.copy()
 face=(X>=-6)&(X<=1)&(Y>=-16)&(Y<=-9);f[face]=b[face]
 source=f.copy();links=[]
 for y in range(164,183):
  for gap in spans((b[y]>0)&(f[y]==0)):
   sy=y;runs=spans(source[sy]>0)
   if not runs:sy=y-1;runs=spans(source[sy]>0)
   assert runs,('new leg source absent',y)
   sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]))
   assert max(int(sr[0])-lo,hi-int(sr[-1]))<=3,('leg alignment beyond3px',y)
   dest=np.arange(lo,hi+1);assert len(dest)<=max(3,2*len(sr))
   sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dest))).astype(int)];f[y,dest]=source[sy,sx]
   links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),sy-160],'index':int(source[sy,xx])}for x,xx in zip(dest,sx))
 full=np.where(f,f,b).astype(np.uint8);own=np.full(b.shape,6,np.uint8)
 own[(Y>=4)|((X>=6)&(Y>=-6))]=8;own[Y<=-7]=5
 own[(X>=-10)&(X<=3)&(Y>=-8)&(Y<=0)]=7;own[face]=5
 # Original native157 uses a Manhattan1/2 aura, white inner13/pink outer7.
 assert np.array_equal(aura(shift(a.layer(156)[0],-1)),a.layer(157)[0])
 energy=a.layer(159)[0];assert np.count_nonzero(energy)==1875
 moved_b=shift(b,-10);moved_f=shift(full,-10)
 body={156:(b,full),157:(aura(shift(b,-1)),aura(shift(full,-1))),158:(np.where(moved_b,ENERGY[moved_b],energy).astype(np.uint8),np.where(moved_f,ENERGY[moved_f],energy).astype(np.uint8))}
 frames=[];rows=[];partial=[]
 for n,(base,fullbody)in body.items():
  dy=0 if n==156 else -1 if n==157 else -10;owners=own if not dy else np.roll(own,dy,0)
  if n==157:
   nearest=distance_transform_edt(shift(full,-1)==0,return_distances=False,return_indices=True);owners=owners[tuple(nearest)]
  assert not np.any((base>0)&(fullbody==0)),('full costume must cover base',n)
  diff=((fullbody!=base)|(np.array([a.words[i]!=a.words[16+i]for i in range(16)])[fullbody]))&(fullbody>0)
  ls={0:base,**{pb:np.where(diff&(owners==pb),fullbody,0).astype(np.uint8)for pb in PBS[1:]}}
  expected=a.rgba(base);expected.alpha_composite(a.rgba(fullbody,16));assert composite(a,ls,15,1).tobytes()==expected.tobytes()
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(owners).save(out/f'owner_{n:03}.png');Image.fromarray(fullbody).save(out/f'fourth_{n:03}_indices.png')
  checks=[{'mask':m,'arm':arm,'components8':int(label(np.array(composite(a,ls,m,arm))[:,:,3]>0,np.ones((3,3)))[1])}for m in range(16)for arm in(1,2)]
  frames.append({'ref':n,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'partial_components':checks,'derived_from':None if n==156 else 156,'translation':[0,dy]})
  rows.append((f'return {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))]))
  partial.append((f'parts {n}',[(name,composite(a,ls,m))for name,m in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
 for i,row in enumerate(rows,1):helper.grid([row],out/f'comparison_{i}.png',6);helper.grid([partial[i-1]],out/f'partial_{i}.png',5)
 Image.fromarray(f_before).save(out/'fourth_source156.png');Image.fromarray(f).save(out/'fourth_registered156.png');Image.fromarray(energy).save(out/'original_energy159.png')
 result={'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'refs':[156,157,158],'frames':frames,'new_body_ref':156,'source_registration':reg.relative_to(ROOT).as_posix(),'shared_new_face_bbox':[-6,-16,2,-8],'leg_registration':links,'base_outer_shared_cells':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere((b>0)&(f==0))],'aura_rule':{'native157_reproduced':True,'metric':'Manhattan','inner':13,'outer':7,'body_translation':[0,-1]},'ascent_rule':{'body_translation':[0,-10],'energy159_exact_sha256':sha(energy.tobytes()),'mapping':ENERGY.tolist(),'old158_body_not_reused':True,'no_old_alpha_clip':True},'native_packed':False,'runtime_verified':False}
 (out/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'frames':3,'components':{q['ref']:sorted({c['components8']for c in q['partial_components']})for q in frames}}))
if __name__=='__main__':main()
