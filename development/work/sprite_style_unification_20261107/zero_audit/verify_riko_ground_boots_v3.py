"""Independent additive two-reference check over boots13 evidence; reader only."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
R=ROOT/'work/sprite_style_unification_20261107/riko';O=Path(__file__).parent/'riko_ground_boots_v3_independent';O.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
proofpath=Path(__file__).parent/'riko_ground_boots_v2_independent/report.json'
assert sha(proofpath.read_bytes())=='568737408bb09cbb6fad85044b624e1b152656f5c9a848f38d6c46cffa5df43d'
prior=json.loads(proofpath.read_text('utf8'));assert prior['passed']
old=(R/'prepared_spin_clothes_v1/PL01_U.ARC').read_bytes();v2=(R/'prepared_ground_boots_v2/PL01_U.ARC').read_bytes();new=(R/'prepared_ground_boots_v3/PL01_U.ARC').read_bytes()
assert sha(old)==prior['parent_sha256'] and sha(v2)==prior['candidate_sha256'];assert sha(new)=='d50e28258d4832fe573ec4aaf1780fe3843b6978ddc897a01ab01d547478a2a5'
assert replace_entry(new,2,entry(old,2))==old
g,ng,c=entry(old,2),entry(new,2),entry(old,3);assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
base=render(old,0,0,71)[0];changed=render(v2,0,0,71)[0];mask=base!=changed;assert mask.sum()==36
extra={67,69};alltargets={61,67,69,71,73,75,77,79,81,91,93,95,97,99,101};support={62,63,64,68,70,72,74,76,78,80,92,94,96,98,100,102,103,104};counts=collections.Counter();consumed=[];rows=[]
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];assert f['tile_count']==nf['tile_count']<=32
  raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
  assert np.array_equal(aa==0,zz==0)
  if not(b==0 and n in alltargets|support):assert raw==nr;counts['non_target_raw_exact']+=1
  if b==0 and n in support:
   ts=sorted({p['tile']for p in composition_frame(c,0,n)['parts']})
   for t in ts:
    y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16])
   consumed.append({'ref':n,'entire_consumed_tiles_exact':ts})
  if b==1 and 42<=n<=49:assert raw==nr;counts['partial8_exact']+=1;continue
  previous=render(v2,b,b*5,n)[0];after=render(new,b,b*5,n)[0];before=render(old,b,b*5,n)[0];counts['display']+=1
  if b==0 and n in extra:
   assert np.array_equal(before[mask],base[mask]);expected=before.copy();expected[mask]=changed[mask];assert np.array_equal(after,expected)
   assert np.array_equal(previous,before);assert np.array_equal(after>0,before>0);counts['added_exact']+=1
   rows.append({'ref':n,'changed_pixels':int((after!=previous).sum()),'exact_same_source_71_boot_material':True})
  else:assert np.array_equal(previous,after);counts['v2_display_exact']+=1
assert counts=={'raw':444,'non_target_raw_exact':411,'display':436,'v2_display_exact':434,'added_exact':2,'partial8_exact':8},counts
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(old,9),row*32);sheet=Image.new('RGB',(768,800),'#64717b');dr=ImageDraw.Draw(sheet)
 for i,n in enumerate(sorted(extra)):
  for col,arc in enumerate((v2,new)):
   pic=rgba(render(arc,0,0,n)[0],words).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(384*col,400*i+16),pic);dr.text((384*col+4,400*i+2),f'{n} '+('v2'if col==0 else'v3'),fill='white')
 sheet.save(O/f'{form}_additional2.png')
result={'passed':True,'candidate_sha256':sha(new),'parent_sha256':sha(old),'prior13_proof_sha256':sha(proofpath.read_bytes()),'v2_sha256':sha(v2),'producer_functions_called':False,'counts':dict(counts),'additional_rows':rows,'added_pixels':72,'shared_support18_consumed_tiles':consumed,'entire_consumed_tiles_checked':sum(len(r['entire_consumed_tiles_exact'])for r in consumed),'composition_palette_audio_static_other_entries_exact':True,'bank1_exact':True,'all_raw_transparency_exact_no_new_gpu_boundary_opacity':True,'raw_tile_counts_and_bank_bounds_exact':True,'visual_review_pending':False,'runtime_verified':False}
result['actually_viewed']=['normal_additional2.png','black_additional2.png']
result['visual_findings']='일반·무채색 추가2자세의 전후 시트를 직접 열람했다.67/69의 발목과 발등 명암이71계열과 이어지며, 발끝·무릎·망토·상체의 원래 모양은 유지된다. 새 실기 또는 전수 미술 완료 판정은 아니다.'
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'consumed_tiles':result['entire_consumed_tiles_checked']}))
