"""Independent fixed-grid generated/native/ARC check; no producer imports."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent/'rin_extension';P=D/'prepared_followthrough01';A=D/'followthrough_registered_v1';sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_spin01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='cf0b079549ea6f1968f3eeb8be37541583f070c134a628c7ea5131fc745dee2a';assert sha(new)=='d3bee17d11b9181d96395fcd0274353f78ef5f7f1bc7c8c5428e573fae3d88b8'
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
reg=json.loads((A/'registration.json').read_text('utf8'));assert reg['source_arc_sha256']==sha(old)
def fixed_source(folder,key):
 info=json.loads((folder/'inputs.json').read_text('utf8'));f=next(f for f in info['frames']if f['key']==key);im=Image.open(folder/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows'];cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)));v=np.array(crop);near=np.zeros(v.shape[:2],np.uint8)
 for y in range(v.shape[0]):near[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,axis=2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(near==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);a=np.zeros((384,384),np.uint8);x0,y0,x1,y1=info['crop'];a[y0:y1,x0:x1]=cell;return a
g1=D/'followthrough01';g2=D/'followthrough_contacts_fix01'
assert sha((g1/'generated.png').read_bytes())==reg['original_new_art_sha256']=='039e810e08a9a50b51746f96da7ca3b4149ae9cd10c7ae70b538fc536148f6cf'
assert sha((g2/'generated.png').read_bytes())==reg['source_generated_sha256']=='7e66e058b6c6ad73c2495e49c899501182f5dea2c7344ab5013ef6d5a8faeadc'
generic=json.loads((g1/'native/registration.json').read_text('utf8'));anchored=json.loads((g1/'anchor_probe/report.json').read_text('utf8'));masters={};provenance=[]
for r in reg['records']:
 key=r['key'];b,n=r['bank'],r['ref'];a=fixed_source(g1,key);gr=next(q for q in generic['records']if q['key']==key);ar=next(q for q in anchored['rows']if q['key']==key);dx=gr['translate'][0]+ar['translation_from_generic'][0];dy=gr['translate'][1]+ar['translation_from_generic'][1];a=np.roll(a,(dy,dx),(0,1));source=ROOT/r['source_native'];assert sha(source.read_bytes())==r['source_native_sha256'];assert np.array_equal(a,np.array(Image.open(source)))
 lower=fixed_source(g2,key);lp=ROOT/r['lower_source_native'];assert sha(lp.read_bytes())==r['lower_source_native_sha256'];assert np.array_equal(lower,np.array(Image.open(lp)))
 z=a.copy();x0,y0,x1,y1=r['lower_region'];m=np.zeros(z.shape,bool);m[y0:y1,x0:x1]=True;z[m]=lower[m]
 for op in r['contact_translations']:
  x0,y0,x1,y1=op['box'];dx,dy=op['translation'];cut=z[y0:y1,x0:x1].copy();z[y0:y1,x0:x1]=0;z[y0+dy:y1+dy,x0+dx:x1+dx]=cut
  if op['retain_source_top_seam_row']:z[y0,x0:x1]=cut[0]
 assert np.array_equal(z[~m],a[~m]);p=A/(key+'_indices.png');assert sha(p.read_bytes())==r['output_sha256'];assert np.array_equal(z,np.array(Image.open(p)));assert not r['old_head_or_body_override']and not r['invented_color'];assert np.nonzero(z)[0].max()==np.nonzero(render(old,b,b*5,n)[0])[0].max();masters[b,n]=z
 provenance.append({'key':key,'new_upper_quantization_translation_exact':True,'new_lower_quantization_registration_exact':True,'outside_lower_region_exact':True,'floor_y':int(np.nonzero(z)[0].max()),'registered_sha256':sha(p.read_bytes())})
targets=dict(masters);assert np.array_equal(render(old,0,0,197)[0],render(old,0,0,212)[0]);targets[0,212]=masters[0,197].copy()
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3);assert replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc)
support={(0,198),(1,144),(1,145),(1,147),(1,157),(1,159)};counts=collections.Counter();consumed=[];gpu=0;changed_parts=[];changed_raw=[]
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
assert counts['raw']==444 and counts['display']==436 and counts['authored_exact']==5 and counts['other_display_exact']==431
assert entry(old,0x10206)==entry(new,0x10206)
for bank in(1,2,3,4,6):
 for n in range(composition_frame(c,bank,0)['bank_frame_count']):assert sem(composition_frame(c,bank,n))==sem(composition_frame(nc,bank,n))
for f in('palette.bin','effect_23.png','effect_24.png'):assert(P/f).read_bytes()==(D/'prepared_spin01'/f).read_bytes()
recipe=json.loads((P/'static_effects.json').read_text('utf8'));before_recipe=json.loads((D/'prepared_spin01/static_effects.json').read_text('utf8'));assert recipe.pop('parts_sha256')==sha(nc);before_recipe.pop('parts_sha256');assert recipe==before_recipe
nativepath=D/'rin205_components_native_checks.json';native=json.loads(nativepath.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
result={'passed':True,'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'candidate_sha256':sha(new),'source_arc_sha256':sha(old),'cumulative_authored_refs':205,'incremental_refs':5,'previous200_preserved':True,'producer_functions_called':False,'source_art_provenance':provenance,'counts':dict(counts),'raw_changed_refs':changed_raw,'part_changed_refs':changed_parts,'support_entire_consumed_tiles':consumed,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'tile_counts_part_counts_bank_bounds_exact':True,'other_entries_palette_sound_exact':True,'static404_semantics_and_texture_exact':True,'partial8_preserved':True,'native_proof_sha256':sha(nativepath.read_bytes()),'user_accepted':False,'runtime_verified':False,'visual_review_pending':True}
(D/'final205_readback_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'support_tiles':sum(len(q['entire_consumed_tiles_exact'])for q in consumed),'gpu':gpu}))
