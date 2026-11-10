"""Independent readback of Nana native-source restoration candidates."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;SRC=ROOT/'work/sprite_style_unification_20261107/nana_audit/native_restore'
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets
from src.psx_frame_edit import frame_coverage
from src.psx_ui_atlas import local_composition
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def merged(a,n):
 v=a.layer(n,0)[0].copy()
 for pb in(8,5,7,6):
  x=a.layer(n,pb)[0];v[x>0]=x[x>0]
 return v
proposal=json.loads((SRC/'prepared_v1/proposal.json').read_text('utf8'));baseline=ROOT/proposal['baseline'];h=hashlib.sha256()
with baseline.open('rb')as f:
 for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
need(h.hexdigest()==proposal['baseline_sha256'],'Parent BIN drift');assets=read_disc(baseline,tuple(proposal['files']))[0];reports={}
for name,spec in proposal['files'].items():
 old=assets[name];new=(ROOT/spec['path']).read_bytes();need(sha(old)==spec['before']and sha(new)==spec['after'],'ARC hash');a,b=Archive(old),Archive(new);need(len(old)==len(new)and replace_entry(new,2,a.g)==old,'Non-graphics mutation');need(bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True),'Banks changed');expected={};targets=set();allowed={}
 metadata=json.loads((SRC/('fourth_registration_v1.json'if name=='PL00_U.ARC'else'ultimate_registration_v1.json')).read_text('utf8'))
 for q in metadata['changes']:
  need(sha((ROOT/q['source_image']).read_bytes())==q['source_sha256'],'Authored source changed');n=q['ref'];changes=q['changes']
  if name=='PL00_U.ARC':
   rel={144:[(144,None),(145,-1)],146:[(146,None),(147,0)],149:[(149,None),(148,0),(150,None),(155,None)],151:[(151,None),(152,0)]}[n]
   for ref,mirror in rel:
    oldlayer=a.layer(ref,8)[0];want=oldlayer.copy()
    for px in changes:
     wx,wy=px['world'];wx=wx if mirror is None else mirror-wx;need(int(oldlayer[160+wy,160+wx])==px['before'],'Mirror or source pixel differs');want[160+wy,160+wx]=px['after']
    expected[ref,8]=want;targets.add(ref)
  else:
   orig=merged(a,n)
   for px in changes:
    wx,wy=px['world'];need(int(orig[160+wy,160+wx])==px['before'],'Canonical merged source')
   for ref in[n,n+1]+([73,74]if n==71 else[]):
    now=merged(a,ref)
    for pb in(0,5):
     oldlayer=a.layer(ref,pb)[0];want=oldlayer.copy()
     for px in changes:
      wx,wy=px['world'];y,x=160+wy,160+wx
      if now[y,x]==px['before']and oldlayer[y,x]in(5,6,7,8,9):want[y,x]=px['after']
     expected[ref,pb]=want
    targets.add(ref)
 # Derive a whitelist of visible native texels directly from each requested layer.
 for(ref,pb),want in expected.items():
  f=a.banks[0]['frames'][ref];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(a.c,pb,ref);cp=local_composition(cp)if pb else cp;cov,size,bb=frame_coverage(raw,f['tile_count'],cp);oldlayer=a.layer(ref,pb)[0]
  for y,x in np.argwhere(want!=oldlayer):
   wx,wy=int(x-160),int(y-160);vis=[(at,sh)for at,sh in cov[(wy-bb[1])*size[0]+wx-bb[0]]if(raw[at]>>sh)&15];need(bool(vis),'No native visible texel');key=(f['offset'],*vis[-1]);value=int(want[y,x]);need(key not in allowed or allowed[key]==value,'Conflicting authored visible texels');allowed[key]=value
 raw_total=unchanged=changed_nibbles=0
 for bi,(ab,bb)in enumerate(zip(a.banks,b.banks)):
  need(len(ab['frames'])==len(bb['frames']),'Ref count changed')
  for of,nf in zip(ab['frames'],bb['frames']):
   need(of['tile_count']==nf['tile_count'],'Tile count changed');ar=decode_stream(a.g,of['offset'],of['limit'],of['tile_count']*128).data;br=decode_stream(b.g,nf['offset'],nf['limit'],nf['tile_count']*128).data;raw_total+=1
   if bi!=0 or of['index']not in targets:need(ar==br,'Non-target raw');unchanged+=1
   else:
    for pos,(av,bv)in enumerate(zip(ar,br)):
     for shift in(0,4):
      ov,nv=(av>>shift)&15,(bv>>shift)&15
      if ov!=nv:need(ov>0 and nv>0 and allowed.get((of['offset'],pos,shift))==nv,'Undocumented native texel');changed_nibbles+=1
 layers=changed_layers=changed_pixels=0
 for ref in range(237):
  if ref in{105,*range(175,183)}:continue
  for pb in(0,5,6,7,8):
   av=a.layer(ref,pb)[0];bv=b.layer(ref,pb)[0];want=expected.get((ref,pb),av);need(np.array_equal(bv,want),f'Target or unselected layer changed {ref}/{pb}');need(np.array_equal(av>0,bv>0),'Alpha changed');layers+=1;count=int(np.count_nonzero(av!=bv));changed_layers+=bool(count);changed_pixels+=count
 reports[name]={'before':sha(old),'after':sha(new),'passed':True,'raw_references':raw_total,'non_target_raw_exact':unchanged,'layers_checked':layers,'changed_layers':changed_layers,'display_layer_pixels_changed':changed_pixels,'native_changed_nibbles_including_shared_refs':changed_nibbles,'unique_allowed_visible_texels':len(allowed),'target_refs':sorted(targets),'composition_palette_audio_other_entries_exact':True,'alpha_tile_counts_and_bank_boundaries_exact':True,'all_native_changes_authorized_by_visible_source_coordinates':True}
report={'passed':True,'scope':'실제 부모 BIN과 동결 후보를 읽고 원화 좌표·실제 raw·모든 유효층 표시를 독립 대조. 제작/패치 함수를 실행하지 않음. 전체 스타일 완료 또는 실기 검증을 뜻하지 않음.','source_bin':proposal['baseline'],'source_sha256':proposal['baseline_sha256'],'projects':reports,'runtime_verified':False}
(D/'nana_restore_independent.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(reports))
