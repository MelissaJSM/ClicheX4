"""Actual generated fixed-grid source to decoded ARC; no producer imports."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ladder_dash01';A=D/'ladder_dash_registered_v1';G=D/'ladder_dash01';sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_followthrough01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8';assert sha(new)=='c2ec4099740eb77cca2d37e4b0f997728e1748a35e47b45475289725ec1dd09b'
reg=json.loads((A/'registration.json').read_text('utf8'));info=json.loads((G/'inputs.json').read_text('utf8'));assert reg['source_arc_sha256']==sha(old);im=Image.open(G/'generated.png').convert('RGBA');assert sha((G/'generated.png').read_bytes())==reg['source_generated_sha256']=='8b0421d987948cee062ceac6f545db0161647561f62d9978317859fb44b0b8cf'
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32);masters={};provenance=[];cw=im.width/2
for row in reg['records']:
 key=row['key'];n=row['ref'];f=next(v for v in info['frames']if v['key']==key);cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*cw),round((cx+1)*cw),round((cy+1)*cw)));v=np.array(crop);nearest=np.zeros(v.shape[:2],np.uint8)
 for yy in range(v.shape[0]):nearest[yy]=1+np.sum((v[yy,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(nearest==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);z=np.zeros((384,384),np.uint8);z[104:200,112:208]=cell;assert np.array_equal(z,np.array(Image.open(G/'native_fixed'/(key+'_indices.png'))))
 rr,gg,bb,aa=np.moveaxis(v.astype(float),-1,0);yy,xx=np.where((rr<gg*.6)&(gg>90)&(gg/(bb+1)>.6)&(gg/(bb+1)<1.15)&(aa>=128));counts=collections.Counter((112+int(x*96/cw),104+int(y*96/cw))for x,y in zip(xx,yy))
 for eye in row['cyan_eye_registration']:
  ex,ey=eye['point'];assert counts[ex,ey]==eye['cyan_source_sample_count']>=15;assert z[ey,ex]==eye['old_index'];assert eye['new_index']==15;z[ey,ex]=15
 dx,dy=row['translation'];z=np.roll(z,(dy,dx),(0,1));assert np.array_equal(z,np.array(Image.open(G/'anchor_probe'/(key+'_indices.png'))))
 if n in(199,202):
  x0,y0,x1,y1=row['head_box'];head=np.zeros_like(z);head[y0:y1,x0:x1]=z[y0:y1,x0:x1];mask=binary_fill_holes(head>0);assert mask.sum()==row['head_mask_pixels'];assert sha((A/(key+'_head_mask.png')).read_bytes())==row['head_mask_sha256'];assert np.array_equal(mask,np.array(Image.open(A/(key+'_head_mask.png')))>0)
  body=z.copy();body[mask]=0;out=np.roll(body,-2,axis=0);out[mask]=head[mask];assert np.array_equal(out[mask],z[mask]);z=out
 assert np.array_equal(z,np.array(Image.open(A/(key+'_indices.png'))));assert sha((A/(key+'_indices.png')).read_bytes())==row['output_sha256'];assert np.nonzero(z)[0].max()==np.nonzero(render(old,0,0,n)[0])[0].max();masters[0,n]=z
 provenance.append({'key':key,'fixed_grid_quantization_exact':True,'source_cyan_eye_samples_verified':True,'new_body_translation_head_and_negative_spaces_exact':n in(199,202),'registered_sha256':row['output_sha256']})
targets={}
for m,refs in[(199,[199,201]),(202,[202,204,206,208,210]),(155,[155]),(156,[156])]:
 for n in refs:assert np.array_equal(render(old,0,0,n)[0],render(old,0,0,m)[0]);targets[0,n]=masters[0,m]
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3);assert replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc)
support={(0,n)for n in(200,203,205,207,209,211,157)};counts=collections.Counter();consumed=[];gpu=0;changed_parts=[];changed_raw=[]
sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];key=b,n;assert f['tile_count']==nf['tile_count']<=32;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1;cp,qp=composition_frame(c,b*5,n),composition_frame(nc,b*5,n);assert len(cp['parts'])==len(qp['parts'])
  if sem(cp)!=sem(qp):assert key in targets;changed_parts.append(key)
  if raw==nr:counts['raw_exact']+=1
  else:assert key in targets or key in support;changed_raw.append(key)
  if key in targets or key in support:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   if key in support:
    ts=sorted({p['tile']for p in cp['parts']})
    for t in ts:
     y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]),('support hidden texel',key,t)
    consumed.append({'key':key,'entire_consumed_tiles_exact':ts})
   for p in qp['parts']:
    t=p['tile'];y,x=t//16*16,t%16*16
    if t%16==0:assert not np.any((aa[y:y+16,x]==0)&(zz[y:y+16,x]!=0))
    if p['flip_y']and t//16%16==0:assert not np.any((aa[y,x:x+16]==0)&(zz[y,x:x+16]!=0))
    gpu+=1
  if b==1 and 42<=n<=49:assert raw==nr and sem(cp)==sem(qp);counts['partial8_exact']+=1;continue
  before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];counts['display']+=1
  if key in targets:assert np.array_equal(after,targets[key]) and not np.array_equal(before,after);counts['authored_exact']+=1
  else:assert np.array_equal(after,before);counts['other_display_exact']+=1
assert counts['raw']==444 and counts['display']==436 and counts['authored_exact']==9 and counts['other_display_exact']==427
assert entry(old,0x10206)==entry(new,0x10206)
for bank in(1,2,3,4,6):
 for n in range(composition_frame(c,bank,0)['bank_frame_count']):assert sem(composition_frame(c,bank,n))==sem(composition_frame(nc,bank,n))
for f in('palette.bin','effect_23.png','effect_24.png'):assert(P/f).read_bytes()==(D/'prepared_followthrough01'/f).read_bytes()
recipe=json.loads((P/'static_effects.json').read_text('utf8'));before_recipe=json.loads((D/'prepared_followthrough01/static_effects.json').read_text('utf8'));assert recipe.pop('parts_sha256')==sha(nc);before_recipe.pop('parts_sha256');assert recipe==before_recipe
nativepath=D/'rin214_components_native_checks.json';native=json.loads(nativepath.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
result={'passed':True,'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'candidate_sha256':sha(new),'source_arc_sha256':sha(old),'cumulative_authored_refs':214,'incremental_refs':9,'previous205_preserved':True,'producer_functions_called':False,'source_art_provenance':provenance,'counts':dict(counts),'raw_changed_refs':changed_raw,'part_changed_refs':changed_parts,'support_entire_consumed_tiles':consumed,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'tile_counts_part_counts_bank_bounds_exact':True,'other_entries_palette_sound_exact':True,'static404_semantics_and_texture_exact':True,'partial8_preserved':True,'native_proof_sha256':sha(nativepath.read_bytes()),'user_accepted':False,'runtime_verified':False,'visual_review_pending':True}
(D/'final214_readback_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'support_tiles':sum(len(q['entire_consumed_tiles_exact'])for q in consumed),'gpu':gpu}))
