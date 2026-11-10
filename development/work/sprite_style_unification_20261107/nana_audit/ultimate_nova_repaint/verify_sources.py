"""노바 생성7고정셀의 실제표본·국소팔·의상·역사효과에서40층을 자체 재구성한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,binary_fill_holes,label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write
def mod(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=mod('nova_source_quant',N/'base_run_repaint/register_page.py');vote=mod('nova_source_vote',N/'ultimate_standing_repaint/prepare_common.py')
read=lambda p:json.loads(p.read_text('utf8'))
def same(z,p):need(np.array_equal(z,np.array(Image.open(p))),'출처 재구성 '+p.relative_to(D).as_posix())
def rows(d):
 m=np.zeros((384,384),bool)
 for y,(x0,x1)in d.items():m[int(y)+160,x0+160:x1+161]=True
 return m
def mean(cell):
 ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255
 resize=lambda z:np.array(Image.fromarray(z.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))
 mass=resize(alpha);return np.stack([resize(rgb[:,:,k]*alpha)/np.maximum(mass,.001)for k in range(3)],2)
def main():
 inp=read(D/'a_inputs_v1/manifest.json');p=ROOT/inp['parent_arc'];need(digest(p)==inp['parent_sha256'],'부모');a=Archive(p.read_bytes());pals={f:np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[s:s+16]],np.float32)for f,s in(('before',16),('after',0))}
 source={};cells={};proof=[]
 for folder,artname,cropkey in(('a_registered_v1','a_v1','source_crop'),('raise215_fixed_v1','raise215_v1','crop')):
  m=read(D/folder/'manifest.json');art=D/artname/'generated.png';need(digest(art)==m.get('source_art_sha256',m.get('source_sha256')),'원화해시');im=Image.open(art).convert('RGBA');need(im.size==(1254,1254),'고정캔버스')
  for q in m['frames']:
   f,n=q['form'],q['ref'];cell=im.crop(q[cropkey]);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pals[f],'area_vote');same(z,D/folder/f'{f}_{n:03}_indices.png');source[folder,f,n]=z;cells[folder,f,n]=cell;proof.append({'source':art.relative_to(ROOT).as_posix(),'source_sha256':digest(art),'crop':q[cropkey],'form':f,'ref':n,'indexed_sha256':sha(z.tobytes())})
 sem={};iris=skin=p15=0;allowed=np.array([1,2,3,4,10,11,12,13])
 for q in read(D/'semantic_samples_v1/manifest.json')['frames']:
  f,n=q['form'],q['ref'];z=source['a_registered_v1',f,n].copy();cell=cells['a_registered_v1',f,n];pal=pals[f];rgb=mean(cell)
  for e in q['iris_removed_upper_samples']:
   x,y=e['world'];v,votes=vote.source_vote(cell,pal,(x,y),{14,15});need(z[y+160,x+160]==14 and v==e['nearest_noniris']and votes==e['noniris_votes'],'실제 비홍채 투표');z[y+160,x+160]=v;iris+=1
  for e in q['skin_rgb_samples']:
   x,y=e['world'];c=rgb[y+48,x+48];v=int(allowed[((pal[allowed]-c)**2).sum(1).argmin()]);need(z[y+160,x+160]==e['old']and v==e['nearest_skin_or_outline']and np.allclose(c,e['source_alpha_weighted_rgb'],atol=1e-6),'실제 하체RGB');z[y+160,x+160]=v;skin+=1
  for e in q['palette15_actual_samples']:
   x,y=e['world'];v,votes=vote.source_vote(cell,pal,(x,y),{15});need(z[y+160,x+160]==15 and v==e['value']and votes==e['votes'],'실제15표본');z[y+160,x+160]=v;p15+=1
  same(z,D/f'semantic_samples_v1/{f}_{n:03}_indices.png');need(np.array_equal(z>0,source['a_registered_v1',f,n]>0),'의미색 알파');sem[f,n]=z
 local={}
 for q in read(D/'raise215_local_probe_v2/manifest.json')['frames']:
  f=q['form'];z=sem[f,215].copy();donor=source['raise215_fixed_v1',f,215];m=rows(q['local_rows']);z[m]=donor[m]
  for e in q['palette15_source_samples']:
   x,y=e['world'];v,votes=vote.source_vote(cells['raise215_fixed_v1',f,215],pals[f],(x,y),{15});need(z[y+160,x+160]==15 and v==e['source_value']and votes==e['votes'],'새팔 실제15표본');z[y+160,x+160]=v;p15+=1
  same(z,D/f'raise215_local_probe_v2/{f}_215_indices.png');need(np.array_equal(z[~m],sem[f,215][~m]),'팔영역밖 보호');local[f,215]=z
 common={};boundary=0
 for q in read(D/'common_probe_v5/manifest.json')['frames']:
  n=q['ref'];src=sem if n==213 else local;b=src['before',n].copy();donor=src['after',n]
  for e in q['source_boundary_links']:
   x,y=e['world'];need(b[y+160,x+160]==e['before_was']and donor[y+160,x+160]==e['source_index'],'허리 실제 경계');b[y+160,x+160]=donor[y+160,x+160];boundary+=1
  m=rows(q['costume_rows']);z=b.copy();z[m]=donor[m]
  for f,v in(('before',b),('after',z)):same(v,D/f'common_probe_v5/{f}_{n:03}_indices.png');need(label(v>0,np.ones((3,3)))[1]==1,'몸체 연결');common[f,n]=v
 art=D/'dash217_v1/generated.png';im=Image.open(art).convert('RGBA');q=read(D/'dash217_registered_v1/manifest.json');need(digest(art)==q['source_art_sha256'],'217원화');body=np.zeros((384,384),np.uint8);body[112:208,112:208]=reg.register(im,(96,96),pals['after'],'area_vote');same(body,D/'dash217_registered_v1/body_217_indices.png');proof.append({'source':art.relative_to(ROOT).as_posix(),'source_sha256':digest(art),'crop':[0,0,*im.size],'ref':217,'form':'common','indexed_sha256':sha(body.tobytes())})
 q=read(D/'dash217_semantic_v1/manifest.json')['iris_actual_sample'];x,y=q['world'];ar=np.array(im);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255;labs=np.empty(alpha.shape,np.uint8)
 for row in range(im.height):labs[row]=1+((rgb[row,:,None]-pals['after'][None,1:])**2).sum(2).argmin(1)
 frac=np.array(Image.fromarray(np.where(labs==14,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))[y+48,x+48]
 need(body[y+160,x+160]==13 and abs(float(frac)-q['green_fraction'])<1e-7 and frac>.28,'217실제홍채');body[y+160,x+160]=14;same(body,D/'dash217_semantic_v1/body_217_indices.png');iris+=1
 hist=ROOT/'work/ver_rin_nana/nana_ultimate_armor/nova_packed_v2/PL02_U.ARC';seedp=ROOT/'work/ultimate_costume_swap_20261105/core/prepared_complete_v1/ver_rin_nana/PL02_U.ARC';m=read(D/'effects_probe_v1/manifest.json');need(digest(hist)==m['historical_sha256']and digest(seedp)==m['swap_seed_sha256'],'역사 효과해시');h=Archive(hist.read_bytes());s=Archive(seedp.read_bytes());oldbody=h.layer(217,5)[0];seed=s.layer(217)[0];remove=binary_dilation(oldbody>0,iterations=1);fx={};effects=[]
 for n,fill in((218,14),(220,7)):
  oldfx=h.layer(n,5)[0];envelope=binary_fill_holes(oldfx>0)
  def rebuild(b):
   v=oldfx.copy();v[remove]=0;v[remove&envelope&(v==0)&(b==0)]=fill;v[b>0]=0;return v
  need(np.array_equal(rebuild(seed),a.layer(n,5)[0]),'역사현재재현');v=rebuild(body);same(v,D/f'effects_probe_v1/effect_{n:03}_indices.png');protected=(~remove)&(body==0);need(np.array_equal(v[protected],oldfx[protected]),'몸영역밖 원효과');need(not np.any((v>0)&(body>0)),'새몸 가림0');fx[n]=v;effects.append({'ref':n,'old_fx_sha256':sha(oldfx.tobytes()),'new_fx_sha256':sha(v.tobytes()),'historical_reproduction_exact':True,'outside_body_domain_exact':True,'opaque':int((v>0).sum())})
 flash=np.zeros_like(body);flash[binary_dilation(seed>0,iterations=2)]=7;flash[seed>0]=6;need(np.array_equal(flash,a.layer(219,5)[0]),'역사219');flash[:]=0;flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6;same(flash,D/'effects_probe_v1/effect_219_indices.png');fx[219]=flash
 tm=read(D/'targets_preview_v1/manifest.json');targets=[];zero=np.zeros_like(body)
 for n in range(213,221):
  if n<217:
   key=n if n%2 else n-1;b,z=common['before',key],common['after',key];diff=np.any(np.array(a.rgba(b,16))!=np.array(a.rgba(z)),2);layers={0:z,5:np.where(diff,b,0).astype(np.uint8),6:zero,7:zero,8:zero}
  else:layers={0:zero if n==219 else body,5:zero if n==217 else fx[n],6:zero,7:zero,8:zero}
  for pb,z in layers.items():same(z,D/f'targets_preview_v1/layer{pb}_{n:03}.png');need(sha(z.tobytes())==tm['targets'][str(n)][str(pb)],'목표해시');targets.append([n,pb,sha(z.tobytes())])
 need(len(proof)==7 and len(targets)==40,'출처범위');out=D/'targets_preview_v1/source_reconstruction.json';need(not out.exists(),'새보고경로');write(out,{'passed':True,'parent_sha256':digest(p),'target_manifest_sha256':digest(D/'targets_preview_v1/manifest.json'),'generated_fixed_cells':proof,'actual_iris_samples':iris,'actual_skin_rgb_samples':skin,'actual_palette15_samples':p15,'actual_shared_boundary_cells':boundary,'effects':effects,'targets_exact':targets,'scope':'생성7고정셀부터 새팔/공통머리·의상/217홍채와 역사효과 규칙→40층 자체재구성. 3고유몸체/5파생참조이며 원US214/216 복원·원효과전체바이트보존·실기 주장 아님.','runtime_verified':False});print(json.dumps({'passed':True,'generated_cells':len(proof),'targets':len(targets),'iris':iris,'skin':skin,'p15':p15,'sha256':digest(out)}))
if __name__=='__main__':main()
