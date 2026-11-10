"""Independent source-art, visible-texel and bounded layout audit; no producer imports."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas,bank_offsets
from src.psx_compress import encode_stream
D=Path(__file__).parent;R=ROOT/'work/sprite_style_unification_20261107/riko';O=D/'riko_ground_boots_v13_independent';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(R/'prepared_ground_boots_v4/PL01_U.ARC').read_bytes();new=(R/'prepared_ground_boots_v13/PL01_U.ARC').read_bytes()
assert sha(old)=='540658ec80aa24415d1df97e37dac0c1a28898907cc8778ba5fa037224e87eb2'
assert sha(new)=='026dd3d47ff05e7a7e9b6ef2330ab06d6be3c617586b6d3aa124a295aee74391'
g,c,ng,nc=entry(old,2),entry(old,3),entry(new,2),entry(new,3)
assert replace_entry(replace_entry(new,2,g),3,c)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
assert bank_offsets(c)==bank_offsets(nc)
reg=json.loads((R/'ground_remaining22/targets02/registration.json').read_text('utf8'))
assert reg['source_sha256']==sha(old)
rects={
 (0,83):[(138,172,149,184),(160,171,173,184)],(0,85):[(137,172,150,184),(162,172,179,184)],
 (0,87):[(143,172,154,184),(167,173,178,184)],(0,89):[(141,173,152,184),(168,174,178,184)],
 (0,105):[(141,173,154,184),(168,173,177,184)],(0,107):[(146,171,156,184),(168,173,180,184)],
 (0,109):[(138,172,149,184),(164,173,174,184)],(0,130):[(145,175,156,184),(168,173,179,184)],
 (0,131):[(139,173,156,184),(170,174,181,184)],(0,155):[(150,175,161,184),(169,174,180,182)],
 (0,156):[(145,172,155,184),(174,175,191,184)],(0,160):[(151,174,160,186),(167,176,181,186)],
 (1,87):[(140,173,155,185),(169,173,182,185)],(1,101):[(139,172,150,185),(161,172,175,185)],
 (1,105):[(141,171,152,184),(162,175,174,185)],(1,130):[(135,171,148,184),(162,175,183,184)]}
words=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32)
masters={};sources=[]
for page in range(23,27):
 p=R/f'ground_boots{page}';info=json.loads((p/'inputs.json').read_text('utf8'));r=json.loads((p/'registered01/registration.json').read_text('utf8'))
 assert info['sha256']==sha(old)==r['source_sha256'];assert sha((p/'generated.png').read_bytes())==r['generated_sha256']
 im=Image.open(p/'generated.png').convert('RGBA');assert im.width/192==im.height/288
 a=np.array(im.resize((192,288),Image.Resampling.NEAREST));q=1+((a[:,:,None,:3].astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2).astype(np.uint8);q[a[:,:,3]<128]=0
 for i,k in enumerate(info['apply_only_keys']):
  k=tuple(k);before=render(old,k[0],k[0]*5,k[1])[0];authored=np.zeros_like(before);authored[112:208,112:208]=q[i//2*96:(i//2+1)*96,i%2*96:(i%2+1)*96]
  region=np.zeros_like(before,bool)
  for x0,y0,x1,y1 in rects[k]:region[y0:y1,x0:x1]=True
  mask=region&np.isin(before,[1,3,7,12,15])&np.isin(authored,[1,3,7,12,15]);target=before.copy();target[mask]=authored[mask]
  for suffix,want in [('indices',target),('authored',authored),('edit_mask',mask.astype('uint8')*255)]:assert np.array_equal(np.array(Image.open(p/f'registered01/b{k[0]}_{k[1]:03}_{suffix}.png')),want)
  masters[k]=target
 sources.append({'page':page,'sha256':sha((p/'generated.png').read_bytes()),'keys':info['apply_only_keys']})
assert len(masters)==16
targets={};aliases=[]
for r in reg['frames']:
 k=r['bank'],r['ref'];m=tuple(r['art_key']);dx,dy=r['native_translation'];before=render(old,k[0],k[0]*5,k[1])[0]
 src=render(old,m[0],m[0]*5,m[1])[0];assert np.array_equal(np.roll(src,(dy,dx),(0,1)),before)
 target=np.roll(masters[m],(dy,dx),(0,1));p=ROOT/r['target'];assert sha(p.read_bytes())==r['target_sha256'];assert np.array_equal(target,np.array(Image.open(p)))
 assert np.array_equal(target>0,before>0);targets[k]=target
 if k!=m:aliases.append({'ref':list(k),'master':list(m),'translation':[dx,dy]})
assert len(targets)==28 and len(aliases)==12
support={(0,n)for n in[84,86,88,90,106,108,110,157,159]}|{(1,n)for n in[102,104,106,128,129]}
counts=collections.Counter();allwrites={};groups={};oldraws={};expectedraws={};usedtiles={};consumed=[];flagchanges=[];changes=[]
for b in(0,1):
 bank=graphics_bank(g,b)
 for f in bank['frames']:
  k=b,f['index'];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;oldraws[k]=raw;group=b,f['offset'];groups.setdefault(group,[]).append(k)
  if k not in targets:continue
  cp=composition_frame(c,b*5,k[1]);actual,size,bb,provenance=compose_indices(raw,f['tile_count'],cp)
  want=targets[k][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]].tobytes();assert len(want)==len(actual)
  writes=allwrites.setdefault(group,{})
  for i,(av,bv)in enumerate(zip(actual,want)):
   if av==bv:continue
   assert av and bv and provenance[i] is not None
   loc=provenance[i]['byte'],provenance[i]['shift'];assert loc not in writes or writes[loc]==bv;writes[loc]=bv
  changes.append({'ref':list(k),'changed_pixels':sum(x!=y for x,y in zip(actual,want))})
for group,keys in groups.items():
 raw=bytearray(oldraws[keys[0]])
 for k in keys:assert oldraws[k]==bytes(raw)
 for(pos,shift),val in allwrites.get(group,{}).items():raw[pos]=raw[pos]&~(15<<shift)|val<<shift
 joint=bytes(raw)
 if group[0]==1 and(1,130)in keys:
  assert set(keys)=={(1,n)for n in[128,129,130,131]}
  assert sha(joint)=='316383242ff8bf6c3a5a813d5cd5410c1e4c69077911c215fefc38da8ffd3559'
  atlas,locs,_=indexed_atlas(joint,len(joint)//128);arr=np.frombuffer(atlas,np.uint8).reshape(-1,256);tile=arr[:16,80:96].copy()
  for yy in range(16):
   for xx in range(16):
    pos,shift=locs[yy*256+80+xx];raw[pos]=raw[pos]&~(15<<shift)|int(tile[yy,15-xx])<<shift
  assert len(encode_stream(joint))-len(encode_stream(bytes(raw)))==4
 for k in keys:expectedraws[k]=bytes(raw)
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b)
 for f,nf in zip(ob['frames'],nb['frames']):
  k=b,f['index'];raw=oldraws[k];nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
  assert f['tile_count']==nf['tile_count']<=32;assert nr==expectedraws[k],('Unexpected hidden/visible texel change',k);counts['raw']+=1
  counts['raw_changed']+=raw!=nr
  cp,np_=composition_frame(c,b*5,k[1]),composition_frame(nc,b*5,k[1]);assert len(cp['parts'])==len(np_['parts'])
  for p,z in zip(cp['parts'],np_['parts']):
   before=bytes(c[p['record_offset']:p['record_offset']+4]);after=bytes(nc[z['record_offset']:z['record_offset']+4])
   if before!=after:
    assert k in{(1,130),(1,131)} and p['tile']==5 and after==bytes([before[0]^64])+before[1:]
    flagchanges.append({'ref':list(k),'tile':5,'old':before.hex(),'new':after.hex()})
  a=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);z=np.frombuffer(indexed_atlas(nr,f['tile_count'])[0],np.uint8).reshape(-1,256)
  if k not in set(targets)|support:assert raw==nr;counts['non_target_raw_exact']+=1
  if k in support:
   ts=sorted({p['tile']for p in cp['parts']})
   for t in ts:
    y,x=t//16*16,t%16*16;assert np.array_equal(a[y:y+16,x:x+16],z[y:y+16,x:x+16])
   consumed.append({'ref':list(k),'entire_consumed_tiles_exact':ts})
  for p in np_['parts']:
   t=p['tile'];y,x=t//16*16,t%16*16
   if t%16==0:assert not np.any((a[y:y+16,x]==0)&(z[y:y+16,x]>0))
   if p['flip_y']and t//16%16==0:assert not np.any((a[y,x:x+16]==0)&(z[y,x:x+16]>0))
  if b==1 and 42<=k[1]<=49:assert raw==nr;counts['partial8_exact']+=1;continue
  before=render(old,b,b*5,k[1])[0];after=render(new,b,b*5,k[1])[0];counts['display']+=1
  assert np.array_equal(after,targets.get(k,before)),k
  counts['target_display_exact'if k in targets else'non_target_display_exact']+=1
assert counts['raw']==444 and counts['display']==436 and counts['target_display_exact']==28 and counts['non_target_display_exact']==408 and counts['partial8_exact']==8
assert len(flagchanges)==2 and len(consumed)==14
assert len(c)==len(nc) and sum(a!=b for a,b in zip(c,nc))==2
for n in(23,24):assert(R/f'prepared_ground_boots_v4/effect_{n}.png').read_bytes()==(R/f'prepared_ground_boots_v13/effect_{n}.png').read_bytes()
result={'passed':True,'candidate_sha256':sha(new),'parent_sha256':sha(old),'producer_functions_called':False,'source_pages':sources,'authored_masters':16,'exact_whole_body_aliases':aliases,'counts':dict(counts),'changes':changes,'support_consumed_tiles':consumed,'support_consumed_tile_count':sum(len(r['entire_consumed_tiles_exact'])for r in consumed),'all_raw_independently_reconstructed':True,'hidden_unconsumed_nibbles_preserved_except_lossless_tile5_orientation':True,'tile5_flip':{'consumers':[130,131],'support128129_tile5_not_consumed':True,'records':flagchanges,'bytes_saved':4},'all_bank_boundaries_tile_counts_fixed':True,'all_other_entries_palette_audio_static_exact':True,'new_gpu_boundary_alpha':0,'visual_review_pending':True,'runtime_verified':False,'scope':'새 원화 16개와 정확한 평행이동 사본 12개에서 부츠 채색만 복원했다. 숨은 픽셀 삭제 없이 타일 5 반전과 조립 플래그 반전으로 화면을 보존하며 4바이트를 절약했다.'}
result['visual_review_pending']=False
result['actually_viewed']=[{'path':str((R/f'prepared_ground_boots_v13/{form}_readback_{i:02}.png').relative_to(ROOT)),'sha256':sha((R/f'prepared_ground_boots_v13/{form}_readback_{i:02}.png').read_bytes())}for form in('normal','black')for i in range(7)]
result['visual_findings']='일반·무채색 14장 모두 실제 열람했다. 부츠의 발등·정강이·발목 밝은 면이 대기의 세분화된 명암과 가까워졌고, 보호한 무릎·발끝 접점과 기존 상체는 이어진다. 특히 101/103은 같은 자세가 좌우로 한 픽셀 이동하며 새 부츠가 함께 유지된다. 기존의 뻗은 다리 길이와 외곽은 보존한 국소 채색 개선이며 모든 동작의 체형 재설계나 실제 플레이 검증을 의미하지 않는다.'
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'changed_pixels':sum(r['changed_pixels']for r in changes),'support_tiles':result['support_consumed_tile_count']}))
