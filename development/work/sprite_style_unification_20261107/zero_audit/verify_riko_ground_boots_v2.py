"""Independent additive four-reference check over frozen boots9 proof."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
R=ROOT/'work/sprite_style_unification_20261107/riko';O=Path(__file__).parent/'riko_ground_boots_v2_independent';O.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest()
proofpath=Path(__file__).parent/'riko_ground_boots_independent/report.json';assert sha(proofpath.read_bytes())=='1440c79c1b2b18ed29fef8bf5965fa945584a37a83480f3b544cdf09a8b7f6c0';prior=json.loads(proofpath.read_text('utf8'));assert prior['passed']
old=(R/'prepared_spin_clothes_v1/PL01_U.ARC').read_bytes();v1=(R/'prepared_ground_boots_v1/PL01_U.ARC').read_bytes();new=(R/'prepared_ground_boots_v2/PL01_U.ARC').read_bytes()
assert sha(old)==prior['parent_sha256'] and sha(v1)==prior['candidate_sha256'];assert sha(new)=='ff9108b32b580bd6e4974970bb1df70e5974cd907bf0573d213d1bd3311b94d4'
assert replace_entry(new,2,entry(old,2))==old
g,ng,c=entry(old,2),entry(new,2),entry(old,3);assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
base=render(old,0,0,71)[0];changed=render(v1,0,0,71)[0];mask=base!=changed;assert mask.sum()==36
extra={73,77,79,81};alltargets={61,71,73,75,77,79,81,91,93,95,97,99,101};support={62,63,64,72,74,76,78,80,92,94,96,98,100,102,103,104};counts=collections.Counter();consumed=[];rows=[]
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];assert f['tile_count']==nf['tile_count']<=32;raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  if not(b==0 and n in alltargets|support):assert raw==nr;counts['non_target_raw_exact']+=1
  if b==0 and n in support:
   a=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);z=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256);ts=sorted({p['tile']for p in composition_frame(c,0,n)['parts']})
   for t in ts:
    y,x=t//16*16,t%16*16;assert np.array_equal(a[y:y+16,x:x+16],z[y:y+16,x:x+16])
   consumed.append({'ref':n,'entire_consumed_tiles_exact':ts})
  if b==1 and 42<=n<=49:assert raw==nr;counts['partial8_exact']+=1;continue
  previous=render(v1,b,b*5,n)[0];after=render(new,b,b*5,n)[0];before=render(old,b,b*5,n)[0];counts['display']+=1
  if b==0 and n in extra:
   assert np.array_equal(before[mask],base[mask]);expected=before.copy();expected[mask]=changed[mask];assert np.array_equal(after,expected);assert np.array_equal(previous,before);assert np.array_equal(after>0,before>0);counts['added_exact']+=1;rows.append({'ref':n,'changed_pixels':int((after!=previous).sum()),'exact_same_source_71_boot_material':True})
  else:assert np.array_equal(previous,after);counts['v1_display_exact']+=1
assert counts=={'raw':444,'non_target_raw_exact':415,'display':436,'v1_display_exact':432,'added_exact':4,'partial8_exact':8},counts
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(old,9),row*32);sheet=Image.new('RGB',(768,400*4),'#64717b');dr=ImageDraw.Draw(sheet)
 for i,n in enumerate(sorted(extra)):
  for col,arc in enumerate((v1,new)):
   pic=rgba(render(arc,0,0,n)[0],words).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(384*col,400*i+16),pic);dr.text((384*col+4,400*i+2),f'{n} '+('v1'if col==0 else'v2'),fill='white')
 sheet.save(O/f'{form}_additional4.png')
result={'passed':True,'candidate_sha256':sha(new),'parent_sha256':sha(old),'prior9_proof_sha256':sha(proofpath.read_bytes()),'v1_sha256':sha(v1),'producer_functions_called':False,'counts':dict(counts),'additional_rows':rows,'added_pixels':144,'shared_support16_consumed_tiles':consumed,'entire_consumed_tiles_checked':sum(len(r['entire_consumed_tiles_exact'])for r in consumed),'composition_palette_audio_static_other_entries_exact':True,'bank1_exact':True,'raw_tile_counts_and_bank_bounds_exact':True,'visual_review_pending':True,'runtime_verified':False}
result['visual_review_pending']=False
result['visual_review']=['normal_additional4.png','black_additional4.png']
result['visual_findings']='두 확대 시트의 추가4자세를 직접 열람했다. 71/75와 같은 발목·발등 명암이73/77/79/81에도 이어지고, 각 망토 변화와 원래 발끝은 그대로다. 전체 동작의 실기 또는 전체 미술 완료 판정은 아니다.'
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'consumed_tiles':result['entire_consumed_tiles_checked']}))
