"""새217의 공통손/하체와 역사ring·220몸효과를 독립 연동한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,binary_fill_holes,distance_transform_edt,label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from prepare_common import box,spans,comp,Y,X
def main():
 m=json.loads((D/'b_inputs_v1/manifest.json').read_text('utf8'));p=ROOT/m['parent_arc'];need(digest(p)==m['parent_sha256'],'부모');a=Archive(p.read_bytes())
 out=D/'dash_layers_probe_v1';out.mkdir(exist_ok=False)
 b=np.array(Image.open(D/'b_registered_v1/base_217_indices.png'));f=np.array(Image.open(D/'b_registered_v1/fourth_217_indices.png'));f0=f.copy()
 shared_boxes=[[-17,-2,-10,4],[-18,3,-12,10],[-8,0,-3,4]];shared=np.zeros(b.shape,bool)
 for bounds in shared_boxes:shared|=box(*bounds)
 f[shared]=b[shared];src=f.copy();links=[]
 for y in range(164,176):
  gaps=spans((b[y]>0)&(f[y]==0)&(np.arange(384)>160));runs=spans((src[y]>0)&(np.arange(384)>160));groups={}
  for gap in gaps:
   need(bool(runs),'같은행 원화');sr=min(runs,key=lambda q:np.min(np.abs(q[:,None]-gap)));groups.setdefault((int(sr[0]),int(sr[-1])),[]).append(gap)
  for(l,r),gs in groups.items():
   lo=min(l,*(int(q[0])for q in gs));hi=max(r,*(int(q[-1])for q in gs));dest=np.arange(lo,hi+1);need(max(l-lo,hi-r)<=2,'2px초과하체정합금지')
   sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];f[y,dest]=src[y,sx]
   links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(src[y,xx])}for x,xx in zip(dest,sx)if x!=xx)
 full=np.where(f,f,b).astype(np.uint8);br=binary_dilation(b>0,iterations=1)&(b==0);fr=binary_dilation(full>0,iterations=1)&(full==0)
 bz=b.copy();fz=full.copy();bz[br]=9;fz[fr]=9;need(not np.any((bz>0)&(fz==0)),'ring포함 포스는기본을모두가림')
 owner=np.full(b.shape,6,np.uint8);owner[(X>=4)|((X>=-5)&(Y<4))]=8;owner[box(-22,-12,-6,4)]=5;owner[box(-20,3,-8,12)|box(-8,0,-3,4)]=7
 _,near=distance_transform_edt(full==0,return_indices=True);owner[fr]=owner[tuple(near[:,fr])]
 paldiff=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[fz];diff=((fz!=bz)|paldiff)&(fz>0)
 ls={0:bz,**{pb:np.where(diff&(owner==pb),fz,0).astype(np.uint8)for pb in(5,6,7,8)}}
 expected=a.rgba(fz,16);need(comp(a,ls,15,1).tobytes()==expected.tobytes(),'217공통층')
 for name,z in(('base_body',b),('fourth_source',f),('fourth_union',full),('base_ring',br.astype(np.uint8)*255),('fourth_ring',fr.astype(np.uint8)*255),('owner',owner)):
  Image.fromarray(z).save(out/f'{name}_217.png')
 for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_217.png')
 # 기존220은현재217의+1y몸을 포함한다. 그 안쪽만효과색9로메우고 새몸을올린다.
 oldbody=np.roll(a.layer(217)[0],1,axis=0);old220=a.layer(220)[0];om=oldbody>0;need(np.array_equal(old220[om],oldbody[om]),'기존220몸+1 exact')
 for pb in(5,6,7,8):need(np.array_equal(a.layer(220,pb)[0],np.roll(a.layer(217,pb)[0],1,axis=0)),f'기존220아머{pb}')
 envelope=binary_fill_holes(old220>0);background=old220.copy();background[om]=0;background[om&envelope]=9
 bodybase=np.roll(bz,1,axis=0);bodyfull=np.roll(fz,1,axis=0);outbase=background.copy();outbase[bodybase>0]=bodybase[bodybase>0];outfull=background.copy();outfull[bodyfull>0]=bodyfull[bodyfull>0]
 l220={0:outbase,**{pb:np.roll(ls[pb],1,axis=0)for pb in(5,6,7,8)}}
 need(comp(a,l220,15,1).tobytes()==a.rgba(outfull,16).tobytes(),'220공통층')
 keep=~om&(bodybase==0);need(np.array_equal(outbase[keep],old220[keep]),'원외부효과보존')
 for pb,z in l220.items():Image.fromarray(z).save(out/f'layer{pb}_220.png')
 Image.fromarray(background).save(out/'effect220_background_indices.png')
 rows=[];checks=[]
 for ref,layers in((217,ls),(220,l220)):
  for mask in range(16):
   for arm in(1,2):im=comp(a,layers,mask,arm);checks.append({'ref':ref,'mask':mask,'arm':arm,'components8':int(label(np.array(im)[:,:,3]>0,np.ones((3,3)))[1]),'rgba_sha256':sha(im.tobytes())})
  for mask in(0,15):rows.append((f'{ref}/{mask}',[('parent',a.composite(ref,mask)[0]),('new native layers',comp(a,layers,mask))]))
 helper.grid([('217 sources',[('base new',a.rgba(b)),('Fourth raw',a.rgba(f0,16)),('common new',a.rgba(full,16)),('new ring base',comp(a,ls,0)),('new ring Fourth',comp(a,ls,15))])],out/'body_comparison.png',6)
 helper.grid(rows,out/'effects_comparison.png',5)
 helper.grid([('217 partial',[(str(mask),comp(a,ls,mask))for mask in(1,2,4,8,10)])],out/'partial.png',7)
 write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_sha256':digest(p),'base_registered_sha256':digest(D/'b_registered_v1/base_217_indices.png'),'fourth_registered_sha256':digest(D/'b_registered_v1/fourth_217_indices.png'),'shared_boxes':shared_boxes,'same_scanline_fourth_links':links,'base_body_pixels':int((b>0).sum()),'fourth_union_pixels':int((full>0).sum()),'ring_pixels':[int(br.sum()),int(fr.sum())],'ring_rule':'역사 C04와같은새몸 Manhattan1 외곽/index9.서로다른의상 외곽은실제union몸기준이며구형ring붙이기없음.','current220_body_shift':[0,1],'current220_body_pixels':int(om.sum()),'current220_external_fx_pixels':int(((old220>0)&~om).sum()),'effect220_rule':'부모의현재217몸+1내부만기존envelope색9로복원후 새217몸/ring+1를합성.바깥효과는새몸이가리는곳외에원좌표·색보존.','new220_external_fx_occluded_by_body':int(((old220>0)&~om&(bodybase>0)).sum()),'new220_open_envelope_pixels':int((envelope&(outbase==0)).sum()),'layer_hashes':{str(n):{str(pb):sha(z.tobytes())for pb,z in layers.items()}for n,layers in((217,ls),(220,l220))},'partial_checks':checks,'native_packed':False,'runtime_verified':False})
 print(json.dumps({'body':[int((b>0).sum()),int((full>0).sum())],'ring':[int(br.sum()),int(fr.sum())],'links':len(links),'partial_components':sorted({x['components8']for x in checks})}))
if __name__=='__main__':main()
