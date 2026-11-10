"""Registered authored standing poses, exact shared recoil and light effect."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,helper
from register_page import register
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
Y,X=np.indices((384,384));Y-=160;X-=160
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
def composite(a,ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def main():
 m=read(D/'inputs01/manifest.json');a=Archive((ROOT/m['parent_arc']).read_bytes());assert sha(a.data)==m['parent_sha256'];src=Image.open(D/'art01/generated.png').convert('RGBA');assert sha((D/'art01/generated.png').read_bytes())=='26765dc823179faae9a24b9102fbccb9aa8d511434e784931b0245a77d3a4711'
 out=D/'joint_layers06';out.mkdir(exist_ok=False);frames=[];proof=[];rows=[];partials=[]
 old89=np.roll(a.layer(89)[0],-1,1);old88=a.layer(88)[0];effect=old89!=old88;assert int(effect.sum())==83 and np.all(old88[effect]==12)
 for pb in(5,6,7,8):assert np.array_equal(np.roll(a.layer(89,pb)[0],-1,1),a.layer(88,pb)[0])
 for n in(89,97):
  bodies={};quant=[]
  for form in('base','fourth'):
   z=np.array(Image.open(D/'registered01'/f'{form}_{n:03}_indices.png'))
   if n==97:
    # Native eyes use one green texel. For the generated lower eyelid cell,
    # resolve its source area vote again without eye-green in the palette.
    # This samples the authored skin rather than painting a new facial row.
    assert z[149,156]==14 and z[150,156]==14
    cell=next(q['cell']for q in m['frames']if q['ref']==n and q['form']==form);cut=src.crop((cell%2*627,cell//2*627,(cell%2+1)*627,(cell//2+1)*627));start=16 if form=='fourth'else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
    rgba=np.array(cut);rgb=rgba[:,:,:3].astype(np.float32);alpha=rgba[:,:,3].astype(np.float32)/255;available=np.array([i for i in range(1,16)if i!=14]);labs=np.zeros(rgba.shape[:2],np.uint8)
    for y in range(len(rgb)):labs[y]=available[((rgb[y,:,None,:]-pal[None,available,:])**2).sum(2).argmin(1)]
    votes=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in available]);own_vote=int(available[votes[:,38,44].argmax()]);v=own_vote if form=='base'else int(bodies['base'][150,156]);assert v in(10,11,12,13),('authored eyelid not skin',form,v);z[150,156]=v;quant.append({'form':form,'world':[-4,-10],'before':14,'after':v,'own_source_vote':own_vote,'source_area_votes':{str(int(i)):float(votes[j,38,44])for j,i in enumerate(available)},'method':'new base lower-eyelid area vote excluding green; shared identical new facial texel into Fourth. Upper eye retained at(-4,-11).'})
   bodies[form]=z
  b,f=bodies['base'],bodies['fourth']
  # Reuse only the new base gun and contact hand in the matching costume.
  shared=poly([[-20,-32],[-11,-32],[-9,-18],[-14,-17],[-20,-23]])if n==89 else poly([[-14,-14],[-8,-14],[-7,-5],[-13,-4]])
  f[shared]=b[shared]
  region=(Y>=7)&(Y<=22)&(X>=-18)&(X<=16)
  if n==97:region&=(Y>=11)|(X<=7) # The pink tip beside the thigh is hair.
  source=f.copy();links=[]
  for y in range(167,183):
   gaps=spans((b[y]>0)&(f[y]==0)&region[y]);runs=spans((source[y]>0)&region[y]);groups={}
   for gap in gaps:
    assert runs,('missing source leg',n,y-160);sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));groups.setdefault((int(sr[0]),int(sr[-1])),[]).append(gap)
   for(l,r),gs in groups.items():
    lo=min(l,*(int(q[0])for q in gs));hi=max(r,*(int(q[-1])for q in gs));dest=np.arange(lo,hi+1);assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1)),('leg bound',n,y-160,l-160,r-160,lo-160,hi-160)
    sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];f[y,dest]=source[y,sx];links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
  own=np.full(b.shape,6,np.uint8);own[(Y>=5)|((X>=8)&(Y>=-5))]=8
  if n==89:
   own[poly([[-20,-33],[-9,-33],[-6,-15],[0,-7],[-6,-2],[-13,-12]])]=7
   own[poly([[3,-8],[12,-7],[14,6],[7,8],[3,2]])]=7
   own[poly([[-9,-22],[7,-22],[12,-14],[7,-7],[-6,-7]])]=5
   own[(X>=6)&(X<=11)&(Y>=-14)&(Y<=-9)]=5
   own[poly([[9,-8],[12,-7],[16,-5],[17,7],[7,8],[7,-4]])]=8
  else:
   own[poly([[-14,-15],[-8,-15],[-7,-6],[5,-7],[7,2],[-8,4],[-14,-1]])]=7
   own[poly([[-8,-21],[5,-21],[10,-14],[7,-6],[-6,-6]])]=5
   own[(X>=6)&(X<=11)&(Y>=-14)&(Y<=-9)]=5
   own[poly([[10,-8],[12,-7],[17,-1],[17,7],[7,8],[7,-4]])]=8
   # The actual raised gun/hand stays with arms even beside the head.
   own[shared]=7
   # These two source-authored pixels are the upper veil edge, not cloth
   # on the torso; body-only equipment otherwise exposes a dark stray mark.
   for x,y in((9,-8),(8,-7)):own[y+160,x+160]=8
  full=np.where(f,f,b).astype(np.uint8);pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];different=((full!=b)|((f>0)&pc))&(full>0)
  ls={0:b,**{pb:np.where(different&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}};expect=a.rgba(b);expect.alpha_composite(a.rgba(f,16));assert composite(a,ls,15,1).tobytes()==expect.tobytes()
  for ref,dx in(((88,-1),(89,0))if n==89 else((97,0),)):
   layers={pb:np.roll(z,dx,1)for pb,z in ls.items()}
   if ref==88:layers[0][effect]=old88[effect]
   for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{ref:03}.png')
   Image.fromarray(np.roll(own,dx,1)).save(out/f'owner_{ref:03}.png')
   frames.append({'ref':ref,'source_ref':n,'translation':[dx,0],'original_effect_overlay_pixels':int(effect.sum())if ref==88 else 0,'layer_hashes':{str(pb):sha(z.tobytes())for pb,z in layers.items()},'components':[{'mask':mask,'arm':arm,'count':int(label(np.array(composite(a,layers,mask,arm))[:,:,3]>0,np.ones((3,3)))[1])}for mask in range(16)for arm in(1,2)]})
   rows.append((f'standing {ref}',[('base idle',a.composite(0)[0]),('new base',composite(a,layers,0)),('Fourth idle',a.composite(0,15)[0]),('new Fourth',composite(a,layers,15))]));partials.append((f'partial {ref}',[(name,composite(a,layers,mask))for name,mask in(('head',1),('body',2),('arms',4),('legs',8),('body legs',10))]))
  proof.append({'ref':n,'eye_registration':quant,'weapon_module':'same new base gun/hand semantic polygon; no old body','shared_module_pixels':int(shared.sum()),'leg_registration':links,'new_base_visible_outside_fourth':int(((b>0)&(f==0)).sum())})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6);helper.grid(partials[i:i+2],out/f'partial_{i//2+1}.png',5)
 (out/'manifest.json').write_text(json.dumps({'parent_arc':m['parent_arc'],'parent_sha256':m['parent_sha256'],'refs':[88,89,97],'frames':frames,'source_registration':proof,'original88_effect':[[int(x-160),int(y-160),int(old88[y,x])]for y,x in np.argwhere(effect)],'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'refs':[88,89,97],'body_components':[{'ref':q['ref'],'counts':sorted(set(c['count']for c in q['components']))}for q in frames]}))
if __name__=='__main__':main()
