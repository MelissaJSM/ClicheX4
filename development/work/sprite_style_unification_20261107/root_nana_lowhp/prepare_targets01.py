"""Register authored low-HP contacts and the existing breathing transform."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit'
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
from scripts.prepare_shibuki_idle import breathe
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda b:hashlib.sha256(b).hexdigest()
m=read(D/'inputs01/manifest.json');a=Archive((ROOT/m['source_arc']).read_bytes());assert sha(a.data)==m['source_arc_sha256']
out=D/'joint_layers03';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));Y-=160;X-=160
def polygon(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def spans(r):
 xs=np.flatnonzero(r);return [] if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def cycle(z,delta):
 v=np.zeros_like(z);v[135:183,136:184]=breathe(z[135:183,136:184],delta)
 assert np.array_equal(v[178:183,136:184],z[178:183,136:184]);return v
def composite(ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
bodies={};mouths={};proof=[]
for form in('base','fourth'):
 p=D/'registered01'/f'{form}_122_indices.png';z=np.array(Image.open(p));sample=np.array(Image.open(D/'registered01'/f'{form}_123_indices.png'))
 assert z[150,156]==12 and sample[150,156]in(1,6)
 mouths[form]=int(sample[150,156]);original=z.copy()
 # Register the authored shoe/ankle module to the old sole; preserve all
 # of its source rows, colors and width. No whole-body stretch.
 z[178:184]=0;z[178:183]=original[179:184]
 assert int(np.nonzero(z)[0].max())==182
 bodies[form]=z;proof.append({'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(p.read_bytes()),'sole_module_source_box':[136,179,184,184],'sole_module_destination_box':[136,178,184,183],'mouth_sample_world':[-4,-10],'mouth_sample_index':mouths[form]})
b=bodies['base'];f=bodies['fourth'];gun=(X>=-11)&(X<=-5)&(Y>=2)&(Y<=9)
f[gun]=b[gun]
# Give the new Fourth bare legs the same occupied footprint as the new
# basic boots, using only bounded samples from the same authored row.
region=(Y>=10)&(Y<=22)&(X>=-8)&(X<=13);source=f.copy();links=[]
for y in range(170,183):
 missing=spans((b[y]>0)&(f[y]==0)&region[y]);fs=spans((f[y]>0)&region[y]);groups={}
 for sb in missing:
  assert fs,('no authored leg',y)
  sf=min(fs,key=lambda s:np.min(np.abs(s[:,None]-sb)));groups.setdefault((int(sf[0]),int(sf[-1])),[]).append(sb)
 for(l,r),runs in groups.items():
  lo=min(l,*(int(q[0])for q in runs));hi=max(r,*(int(q[-1])for q in runs));dst=np.arange(lo,hi+1)
  assert max(l-lo,hi-r)<=2 and len(dst)<=max(3,(r-l+1)*2),('leg registration bound',y,l,r,lo,hi)
  sample=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dst))).astype(int)]
  f[y,dst]=source[y,sample]
  links.extend({'dest':[int(x)-160,y-160],'source':[int(sx)-160,y-160],'index':int(source[y,sx])}for x,sx in zip(dst,sample))
assert not np.any((b>0)&(f==0)&region)
owner=np.full(b.shape,6,np.uint8);owner[(Y>=4)|((X>=5)&(Y>=-7))]=8
owner[polygon([[-10,-5],[-5,-7],[-3,0],[-4,6],[-8,10],[-11,10]])]=7
owner[polygon([[-4,-5],[8,-5],[11,0],[8,2],[-4,0]])]=7
owner[(X>=-8)&(X<8)&(Y>=-22)&(Y<-6)]=5
# The rear veil belongs to the leg equipment as in the accepted costume.
# Its upper-to-lower section must have one owner; a rectangular crop had
# left an isolated-looking triangle on body-only partial equipment.
owner[polygon([[3,-18],[7,-18],[13,-12],[18,-7],[18,9],[8,9],[5,-4]])]=8
frames=[];rows=[];partials=[]
for n,delta in((120,1),(122,0),(124,-1)):
 for opened in(0,1):
  ref=n+opened;body=b.copy();costume=f.copy()
  if opened:body[150,156]=mouths['base'];costume[150,156]=mouths['fourth']
  body=cycle(body,delta);costume=cycle(costume,delta);own=cycle(owner,delta)
  full=np.where(costume,costume,body).astype(np.uint8);pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
  change=((full!=body)|((costume>0)&pc))&(full>0)
  ls={0:body,**{pb:np.where(change&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  expect=a.rgba(body);expect.alpha_composite(a.rgba(costume,16));assert composite(ls,15,1).tobytes()==expect.tobytes()
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{ref:03}.png')
  Image.fromarray(own).save(out/f'owner_{ref:03}.png')
  frames.append({'ref':ref,'breathing_delta':delta,'mouth_open':bool(opened),'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in ls.items()},'components':[{'mask':mask,'arm':arm,'count':int(label(np.array(composite(ls,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]})
  rows.append((f'low HP {ref}',[('base idle',a.composite(0)[0]),('new base',composite(ls,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(ls,15))]))
  partials.append((f'partial {ref}',[(name,composite(ls,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
for i in range(0,len(rows),2):
 helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6);helper.grid(partials[i:i+2],out/f'partial_{i//2+1}.png',5)
(out/'manifest.json').write_text(json.dumps({'parent_arc':m['source_arc'],'parent_sha256':m['source_arc_sha256'],'refs':list(range(120,126)),'frames':frames,'source_registration':proof,'gun_module_source':'new base 122 rectangle world[-11,2,-4,10]','leg_registration':links,'body_from_closed_122_only':True,'breathing_source':'scripts.prepare_shibuki_idle.breathe','native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'refs':list(range(120,126)),'component_issues':[{'ref':q['ref'],'issues':[c for c in q['components']if c['count']>1]}for q in frames if any(c['count']>1 for c in q['components'])]}))
