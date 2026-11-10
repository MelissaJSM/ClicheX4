"""Register new ride-chaser art into independently wearable native layers."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest()
Y,X=np.indices((384,384));Y-=160;X-=160
PBS=(0,5,6,7,8);KEYS=(162,166,170,174)
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
def spans(row):
 xs=np.flatnonzero(row);return [] if not len(xs) else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def rect(b):
 x0,y0,x1,y1=b;return (X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def main():
 parent=W/'root_nana_return/packed_return03/PL00_U.ARC';a=Archive(parent.read_bytes())
 assert sha(a.data)=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9'
 out=D/'joint_targets03';out.mkdir(exist_ok=False)
 base_layers={};sources=[]
 faces={162:(-18,-12,-9,-4),166:(-17,-14,-8,-6),170:(-16,-18,-7,-10),174:(-12,-22,-3,-14)}
 hands={162:(-22,-1,-13,3),166:(-22,-2,-14,6),170:(-19,-7,-10,-2),174:(-17,-10,-8,-4)}
 leg_start={162:6,166:5,170:1,174:-4}
 head_bottom={162:-5,166:-7,170:-11,174:-14}
 for n in KEYS:
  reg=D/('registered_a01' if n<170 else 'registered_b01')
  b=np.array(Image.open(reg/f'base_{n:03}_indices.png'));f=np.array(Image.open(reg/f'fourth_{n:03}_indices.png'))
  face=rect(faces[n]);hand=rect(hands[n])
  if n==174:b[face]=f[face]
  else:f[face]=b[face]
  f[hand]=b[hand]
  source=f.copy();links=[]
  for y in range(160+leg_start[n],190):
   for gap in spans((b[y]>0)&(f[y]==0)):
    candidates=[]
    for sy in (y,y-1,y+1):
     for sr in spans(source[sy]>0):
      lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]))
      extent=max(int(sr[0])-lo,hi-int(sr[-1]))
      if extent<=3 and hi-lo+1<=max(3,2*len(sr)):
       candidates.append((abs(sy-y),extent,sy,sr,lo,hi))
    assert candidates,('no local new leg correspondence',n,y)
    _,_,sy,sr,lo,hi=min(candidates,key=lambda c:c[:2])
    dest=np.arange(lo,hi+1)
    sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dest))).astype(int)]
    f[y,dest]=source[sy,sx]
    links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),sy-160],'index':int(source[sy,xx])}for x,xx in zip(dest,sx))
  full=np.where(f,f,b).astype(np.uint8)
  own=np.full(b.shape,6,np.uint8)
  own[Y>=leg_start[n]]=8
  # Rear veil is the approved leg accessory. Cap/front hair belongs to head.
  own[(X>=-1)&(Y>=head_bottom[n]-2)]=8
  own[Y<=head_bottom[n]]=5
  own[rect((hands[n][0],hands[n][1]-2,-4,hands[n][3]+1))]=7
  own[face]=5
  diff=((full!=b)|np.array([a.words[i]!=a.words[16+i] for i in range(16)])[full])&(full>0)
  ls={0:b,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
  expected=a.rgba(b);expected.alpha_composite(a.rgba(full,16))
  assert composite(a,ls,15,1).tobytes()==expected.tobytes()
  base_layers[n]=(ls,own,full)
  Image.fromarray(f).save(out/f'fourth_registered_{n:03}.png')
  sources.append({'ref':n,'registration':reg.relative_to(ROOT).as_posix(),'shared_new_face':faces[n],'face_source_form':'fourth'if n==174 else'base','shared_new_hand':hands[n],'leg_registration':links,'base_outer_shared_cells':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere((b>0)&(f==0))]})
 frames=[]
 for n in range(162,175):
  k=162 if n<166 else 166 if n<170 else 170 if n<174 else 174
  ls,own,full=base_layers[k];dy=DY[n];ls={pb:np.roll(z,dy,axis=0)for pb,z in ls.items()}
  # Alias geometry is an actual byte/pixel identity in the parent, not an invented interpolation.
  for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],np.roll(a.layer(k,pb)[0],dy,0)),('parent alias mismatch',n,pb)
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  Image.fromarray(np.roll(own,dy,0)).save(out/f'owner_{n:03}.png')
  checks=[{'mask':m,'arm':arm,'components8':int(label(np.array(composite(a,ls,m,arm))[:,:,3]>0,np.ones((3,3)))[1])}for m in range(16)for arm in(1,2)]
  frames.append({'ref':n,'source_key':k,'translation':[0,dy],'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'partial_components':checks})
  if n in KEYS:
   helper.grid([(f'ride {n}',[('base idle',a.composite(0)[0]),('new base',composite(a,ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,ls,15))])],out/f'comparison_{n}.png',6)
   helper.grid([(f'parts {n}',[(name,composite(a,ls,m))for name,m in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))])],out/f'partial_{n}.png',5)
 report={'parent_arc':parent.relative_to(ROOT).as_posix(),'parent_sha256':sha(a.data),'refs':list(range(162,175)),'frames':frames,'sources':sources,'original_alpha_not_clipped':True,'native_packed':False,'runtime_verified':False}
 (out/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'refs':13,'unique_new_bodies':8,'components':{q['ref']:sorted({c['components8']for c in q['partial_components']})for q in frames},'leg_links':{q['ref']:len(q['leg_registration'])for q in sources}}))
if __name__=='__main__':main()
