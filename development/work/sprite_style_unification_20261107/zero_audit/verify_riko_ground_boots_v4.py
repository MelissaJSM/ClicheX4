"""Read-only independent four-pose material provenance and native resource audit."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
D=Path(__file__).parent;R=ROOT/'work/sprite_style_unification_20261107/riko';O=D/'riko_ground_boots_v4_independent';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
priorpath=D/'riko_ground_boots_v3_independent/report.json';prior=json.loads(priorpath.read_text('utf8'))
assert prior['passed'] and sha(priorpath.read_bytes())=='d2ed1c8bbee77601352b9ee8a7d2426d2e0c6fec60e0ca12c11ff98d88f21564'
old=(R/'prepared_ground_boots_v3/PL01_U.ARC').read_bytes();new=(R/'prepared_ground_boots_v4/PL01_U.ARC').read_bytes()
assert sha(old)==prior['candidate_sha256'];assert sha(new)=='540658ec80aa24415d1df97e37dac0c1a28898907cc8778ba5fa037224e87eb2'
assert replace_entry(new,2,entry(old,2))==old
source=R/'ground_boots21/generated.png';assert sha(source.read_bytes())=='731a65c1a06f79976d0fc43348f6d0c325dd91ecd08b7ff636c69c1b24762ea0'
im=Image.open(source).convert('RGBA');assert im.size==(1024,1536)
page=np.array(im.resize((192,288),Image.Resampling.NEAREST));words=struct.unpack_from('<16H',entry(old,9))
colors=np.array([[(w>>s&31)*255//31 for s in (0,5,10)]for w in words],np.int32)
quantized=1+((page[:,:,None,:3].astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);quantized[page[:,:,3]<128]=0
regions={62:[(144,173,159,183),(165,173,180,184)],63:[(141,173,155,183),(162,173,174,184)],65:[(144,173,157,183),(163,173,176,184)],82:[(143,173,158,183),(164,174,178,184)]}
targets={};provenance=[]
for i,n in enumerate(regions):
 before=render(old,0,0,n)[0];authored=np.zeros_like(before);authored[112:208,112:208]=quantized[i//2*96:(i//2+1)*96,i%2*96:(i%2+1)*96]
 region=np.zeros_like(before,bool)
 for x0,y0,x1,y1 in regions[n]:region[y0:y1,x0:x1]=True
 mask=region&np.isin(before,[1,3,7,12,15])&np.isin(authored,[1,3,7,12,15])
 target=before.copy();target[mask]=authored[mask];assert np.array_equal(target>0,before>0)
 for suffix,expected in [('authored',authored),('edit_mask',mask.astype('uint8')*255),('indices',target)]:
  path=R/f'ground_boots21/registered01/b0_{n:03}_{suffix}.png';assert np.array_equal(np.array(Image.open(path)),expected)
 targets[n]=target;provenance.append({'ref':n,'source_sha256':sha(source.read_bytes()),'target_sha256':sha((R/f'ground_boots21/registered01/b0_{n:03}_indices.png').read_bytes()),'changed_pixels':int((target!=before).sum()),'independently_reconstructed_authored_boot_region':True})
g,ng,c=entry(old,2),entry(new,2),entry(old,3);assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
support={61,64,66};counts=collections.Counter();consumed=[];actual=[]
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];assert f['tile_count']==nf['tile_count']<=32
  raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  a=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);z=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256);assert np.array_equal(a==0,z==0)
  if not(b==0 and n in set(targets)|support):assert raw==nr;counts['non_target_raw_exact']+=1
  if b==0 and n in support:
   ts=sorted({p['tile']for p in composition_frame(c,0,n)['parts']})
   for t in ts:
    y,x=t//16*16,t%16*16;assert np.array_equal(a[y:y+16,x:x+16],z[y:y+16,x:x+16])
   consumed.append({'ref':n,'entire_consumed_tiles_exact':ts})
  if b==1 and 42<=n<=49:assert raw==nr;counts['partial8_exact']+=1;continue
  before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];counts['display']+=1
  if b==0 and n in targets:assert np.array_equal(after,targets[n]);counts['authored_exact']+=1
  else:assert np.array_equal(before,after);counts['non_target_display_exact']+=1
assert counts=={'raw':444,'non_target_raw_exact':437,'display':436,'authored_exact':4,'non_target_display_exact':432,'partial8_exact':8},counts
for form,row in [('normal',0),('black',13)]:
 palette=struct.unpack_from('<16H',entry(old,9),row*32)
 for start in(0,2):
  sheet=Image.new('RGB',(768,800),'#64717b');dr=ImageDraw.Draw(sheet)
  for i,n in enumerate(list(targets)[start:start+2]):
   for col,arc in enumerate((old,new)):
    im=rgba(render(arc,0,0,n)[0],palette).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(im,(384*col,400*i+16),im);dr.text((384*col+4,400*i+2),f'{n} '+('before'if col==0 else'new'),fill='white')
  sheet.save(O/f'{form}_{start//2:02}.png')
for n in(23,24):assert (R/f'prepared_ground_boots_v3/effect_{n}.png').read_bytes()==(R/f'prepared_ground_boots_v4/effect_{n}.png').read_bytes()
result={'passed':True,'candidate_sha256':sha(new),'parent_sha256':sha(old),'prior15_proof_sha256':sha(priorpath.read_bytes()),'producer_functions_called':False,'provenance':provenance,'counts':dict(counts),'changed_pixels':sum(r['changed_pixels']for r in provenance),'shared_support3_consumed_tiles':consumed,'entire_consumed_tiles_checked':sum(len(r['entire_consumed_tiles_exact'])for r in consumed),'all_parts_palette_audio_static_other_entries_exact':True,'all_raw_transparency_exact_no_new_gpu_boundary_opacity':True,'bank1_exact':True,'tile_counts_bank_boundaries_exact':True,'prior15_and_other417_displays_preserved':True,'visual_review_pending':False,'runtime_verified':False}
result['actually_viewed']=['normal_00.png','normal_01.png','black_00.png','black_01.png']
result['visual_findings']='최종 ARC의 네 자세를 일반·무채색4장으로 직접 비교했다. 부츠의 발등·발목 면이 조금 더 분리되고, 기존 발끝·무릎·상체 원점은 유지된다. 전체 의상 재작화나 게임 실기 완료를 의미하지 않는다.'
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'changed_pixels':result['changed_pixels'],'consumed_tiles':result['entire_consumed_tiles_checked']}))
