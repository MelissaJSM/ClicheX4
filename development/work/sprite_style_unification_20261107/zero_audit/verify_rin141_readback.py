"""Independent generated/native/ARC checks; no producer function calls."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent/'rin_extension';P=D/'prepared_ground_wall_v1';A=D/'after122_registered_v1';sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_ground_first_v1/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(old)=='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1';assert sha(new)=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
reg=json.loads((A/'registration.json').read_text('utf8'));assert reg['source_arc_sha256']==sha(old)
masters={};provenance=[]
for r in reg['records']:
 key=r['key'];b,n=r['bank'],r['ref'];source=ROOT/r['source_native'];assert sha(source.read_bytes())==r['source_native_sha256'];folder=source.parent.parent;gen=folder/'generated.png';assert sha(gen.read_bytes())==r['generated_sha256'];info=json.loads((folder/'inputs.json').read_text('utf8'));native=json.loads((folder/'native/registration.json').read_text('utf8'));f=next(f for f in info['frames']if f['ref']==n);nr=next(f for f in native['records']if f['ref']==n)
 im=Image.open(gen).convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows'];cx,cy=f['cell'];crop=im.crop((round(cx*cw),round(cy*ch),round((cx+1)*cw),round((cy+1)*ch)));v=np.array(crop);near=np.zeros(v.shape[:2],np.uint8)
 for y in range(v.shape[0]):near[y]=1+np.sum((v[y,:,:3,None].transpose(0,2,1).astype(np.int32)-colors[None,:,:])**2,axis=2).argmin(1)
 votes=np.stack([np.array(Image.fromarray(np.where(near==i,v[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);alpha=np.array(crop.getchannel('A').resize((96,96),Image.Resampling.BOX));cell=np.where(alpha>=128,votes.argmax(0)+1,0).astype(np.uint8);a=np.zeros((384,384),np.uint8);a[112:208,112:208]=cell;dx,dy=nr['translate'];a=np.roll(a,(dy,dx),(0,1));assert np.array_equal(a,np.array(Image.open(source)))
 for op in r['operations']:
  if 'source_iris_cell'in op:
   rr,gg,bb,al=[v[:,:,i].astype(float)for i in range(4)];ratio=np.divide(gg,bb,out=np.zeros_like(gg),where=bb>0);y,x=np.where((al>=128)&(rr<gg*.6)&(gg>90)&(ratio>.6)&(ratio<1.15));vv=collections.Counter(zip((112+x*96/cw).astype(int).tolist(),(112+y*96/ch+nr['translate'][1]).astype(int).tolist()));pos=tuple(op['source_iris_cell']);assert vv[pos]==op['actual_cyan_source_pixels']>=10;a[pos[1],pos[0]]=15
  elif 'whole_translation'in op:
   dx,dy=op['whole_translation'];a=np.roll(a,(dy,dx),(0,1))
  else:
   mask=Image.new('1',(384,384));ImageDraw.Draw(mask).polygon(op['polygon'],fill=1);mask=np.array(mask,bool);z=a.copy();a[mask]=0;y,x=np.where(mask);dx,dy=op['translation'];a[y+dy,x+dx]=z[y,x]
 p=A/(key+'_indices.png');assert sha(p.read_bytes())==r['output_sha256'];assert np.array_equal(a,np.array(Image.open(p)));assert not r['old_body_or_head_override'] and not r['manually_invented_color'];masters[b,n]=a;provenance.append({'key':key,'generated_sha256':sha(gen.read_bytes()),'native_sha256':sha(source.read_bytes()),'registered_sha256':sha(p.read_bytes()),'source_quantization_and_registration_reconstructed':True})
mapping={(0,n):(0,m)for m,refs in[(71,[71]),(73,[73,75,77,79,81]),(82,[82]),(131,[131,132])]for n in refs};mapping.update({(1,n):(1,m)for m,refs in[(50,[50]),(51,[51,53]),(54,[54,56]),(57,[57,59,61,63,65])]for n in refs})
targets={}
for (b,n),(bb,m)in mapping.items():assert np.array_equal(render(old,b,b*5,n)[0],render(old,bb,bb*5,m)[0]);targets[b,n]=masters[bb,m]
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3);assert replace_entry(replace_entry(new,2,g),3,c)==old;assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)and bank_offsets(c)==bank_offsets(nc)
support={(0,n)for n in(72,74,76,78,80)}|{(1,n)for n in(52,55,58,60,62,64)};counts=collections.Counter();consumed=[];gpu=0;changed_parts=[];changed_raw=[]
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
assert counts['raw']==444 and counts['display']==436 and counts['authored_exact']==19 and counts['other_display_exact']==417
assert entry(old,0x10206)==entry(new,0x10206)
for bank in(1,2,3,4,6):
 for n in range(composition_frame(c,bank,0)['bank_frame_count']):assert sem(composition_frame(c,bank,n))==sem(composition_frame(nc,bank,n))
for f in('palette.bin','effect_23.png','effect_24.png'):assert(P/f).read_bytes()==(D/'prepared_ground_first_v1'/f).read_bytes()
recipe=json.loads((P/'static_effects.json').read_text('utf8'));before_recipe=json.loads((D/'prepared_ground_first_v1/static_effects.json').read_text('utf8'));assert recipe.pop('parts_sha256')==sha(nc);before_recipe.pop('parts_sha256');assert recipe==before_recipe
nativepath=D/'rin141_components_native_checks.json';native=json.loads(nativepath.read_text('utf8'));assert native['passed']and native['resources']['PL01_U.ARC']['candidate_sha256']==sha(new)
result={'passed':True,'candidate':str((P/'PL01_U.ARC').relative_to(ROOT)),'candidate_sha256':sha(new),'source_arc_sha256':sha(old),'cumulative_authored_refs':141,'incremental_refs':19,'previous122_preserved':True,'producer_functions_called':False,'source_art_provenance':provenance,'counts':dict(counts),'raw_changed_refs':changed_raw,'part_changed_refs':changed_parts,'support_entire_consumed_tiles':consumed,'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'tile_counts_part_counts_bank_bounds_exact':True,'other_entries_palette_sound_exact':True,'static404_semantics_and_texture_exact':True,'partial8_preserved':True,'native_proof_sha256':sha(nativepath.read_bytes()),'user_accepted':False,'runtime_verified':False,'visual_review_pending':True}
(D/'final141_readback_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'support_tiles':sum(len(q['entire_consumed_tiles_exact'])for q in consumed),'gpu':gpu}))
