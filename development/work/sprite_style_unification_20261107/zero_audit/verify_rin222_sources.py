"""원화 고정 셀부터 새8의 실제 ARC 표시까지 별도로 재구성한다."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_fill_holes
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
D=Path(__file__).parent/'rin_extension';A=D/'dash_saber_registered_v1';P=D/'prepared_dash_saber01'
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_ladder_dash01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes()
assert sha(old)=='c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b'
assert sha(new)=='94b24181ee1d6ce463f1647e89f58fcf29c57e8eb8cc6ede457cc46e22fc36da'
reg=json.loads((A/'registration.json').read_text('utf8'));assert reg['source_arc_sha256']==sha(old)
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
native={};source_proofs=[]
for source in reg['generated']:
 path=ROOT/source['path'];assert sha(path.read_bytes())==source['sha256'];info=json.loads((path.parent/'inputs.json').read_text('utf8'))
 assert info['archive_sha256']==sha(old) and info['palette_words']==list(pal)
 im=Image.open(path).convert('RGBA');assert im.width==im.height;cw=im.width/2
 for f in info['frames']:
  cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*cw),round((cx+1)*cw),round((cy+1)*cw)));v=np.array(crop);nearest=np.zeros(v.shape[:2],np.uint8)
  for yy in range(v.shape[0]):nearest[yy]=1+np.sum((v[yy,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,2).argmin(1)
  votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
  alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8)
  x0,y0,x1,y1=info['crop'];z=np.zeros((384,384),np.uint8);z[y0:y1,x0:x1]=cell
  assert np.array_equal(z,np.array(Image.open(path.parent/'native_fixed'/(f['key']+'_indices.png'))))
  native[path.parent.name,f['ref']]=z
  source_proofs.append({'generated':str(path.relative_to(ROOT)),'sha256':source['sha256'],'key':f['key'],'fixed_cell_quantization_exact':True,'actual_dimensions':im.size})
masters={};shifts={158:(0,-4),160:(0,-4),162:(0,2),164:(0,1),166:(0,-3),168:(0,-2),170:(3,-1),172:(2,-1)}
for n in range(158,174,2):
 folder='dash_saber_followup01'if n<=164 else'dash_saber_followup02';dx,dy=shifts[n];z=np.roll(native[folder,n],(dy,dx),(0,1));assert np.array_equal(z,np.array(Image.open(D/folder/'anchor_probe'/f'b0_{n:03}_indices.png')))
 if n==164:
  im=Image.open(D/folder/'generated.png').convert('RGBA');cw=im.width/2;v=np.array(im.crop((round(cw),round(cw),im.width,im.height))).astype(float);r,g,b,a=np.moveaxis(v,-1,0)
  yy,xx=np.where((r<g*.6)&(g>90)&(g/(b+1)>.6)&(g/(b+1)<1.15)&(a>=128));ct=collections.Counter((112+int(x*96/cw),104+int(y*96/cw))for x,y in zip(xx,yy));assert ct.most_common(1)[0]==((160,145),28)
  assert z[146,160]==3;z[146,160]=15
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon([(141,134),(167,134),(167,152),(153,152),(148,149),(147,147),(141,146)],fill=1)
  mask=binary_fill_holes(np.array(m,bool)&(z>0));assert np.array_equal(mask,np.array(Image.open(D/folder/'registered_probe_v2/b0_164_head_mask.png'))>0)
  head=np.where(mask,z,0);out=np.where(mask,0,z);moved=np.roll(head,2,axis=0);out[np.roll(mask,2,axis=0)]=moved[np.roll(mask,2,axis=0)];z=out
 if n in(166,170,172):
  local=D/'dash_saber_followup02/local_legs01';info=json.loads((local/'registered_probe_v2/registration.json').read_text('utf8'));row=next(r for r in info['records']if r['key']==f'b0_{n:03}')
  assert np.array_equal(z,np.array(Image.open(local/f'b0_{n:03}_before_indices.png')))
  ux,uy=row['upper_rigid_translation'];upper=np.roll(z,(uy,ux),(0,1));lx,ly=row['lower_rigid_translation'];lower=np.roll(native['local_legs01',n],(ly,lx),(0,1));mask=np.zeros_like(z,bool);mask[row['all_y_from']:]=True
  for x0,y0,x1,y1 in row['leg_regions']:mask[y0:y1,x0:x1]=True
  assert np.array_equal(mask,np.array(Image.open(local/'registered_probe_v2'/f'b0_{n:03}_leg_mask.png'))>0)
  z=np.where(mask,lower,upper).astype(np.uint8);assert np.array_equal(z[~mask],upper[~mask])
 final=next(r for r in reg['records']if r['key']==f'b0_{n:03}');assert sha((ROOT/final['registration']).read_bytes())==final['registration_sha256']
 assert sha((A/f'b0_{n:03}_indices.png').read_bytes())==final['output_sha256']==final['source_sha256'];assert np.array_equal(z,np.array(Image.open(A/f'b0_{n:03}_indices.png')))
 assert np.array_equal(z,render(new,0,0,n)[0]);assert np.nonzero(z)[0].max()==np.nonzero(render(old,0,0,n)[0])[0].max();masters[n]=z
result={'passed':True,'candidate_sha256':sha(new),'source_arc_sha256':sha(old),'producer_functions_called':False,'source_cells_rebuilt':len(source_proofs),'new_art_refs':sorted(masters),'generated_sources':reg['generated'],'source_proofs':source_proofs,'source_eye_samples_verified':28,'new_head_negative_space_translation_exact':True,'local_legs_source_registration_exact':True,'all8_floor_anchors_exact':True,'old_head_override':False,'runtime_verified':False,'user_accepted':False}
(D/'rin222_source_proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'cells':len(source_proofs),'art_refs':len(masters)}))
