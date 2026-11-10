"""최종 시부키 141 교정 2자원을 독립 디코드/파츠/색상 합성으로 검사한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts import restore_shibuki_special_detail as r
from src.psx_player import graphics_bank,bank_offsets,composition_frame,indexed_atlas,decode_stream
from src.psx_ui_atlas import local_composition

D=ROOT/'work/sprite_consistency_20261105/x/arrival141_history/prepared_v1'
q=json.loads((D/'proposal.json').read_text('utf8'))
EXPECTED={'PL00_U.ARC':'ec683d1d980fedc35c63f73a29da3424d94a4d2c6cf362863d33d7720acf6fe3',
          'PL02_U.ARC':'838550cf4441af6d851b39736aec0c529dddb905d21d5dadb3cbaf7c227b48a4'}
SOURCES={'PL00_U.ARC':'075b03a71b6ce9df91e5db2de44f7e715c51c60b681284e7df24df6a225e50aa',
         'PL02_U.ARC':'3228c2b8d1a339cac2256f2ba5229f5ece6a9de4e22608b31fbe14988be1323a'}

def records(comp):
 return [{k:v for k,v in pp.items() if k not in('index','record_offset')}for pp in comp['parts']]

def layer(raw,count,c,cb,n):
 comp=composition_frame(c,cb,n)
 if cb:comp=local_composition(comp)
 out=np.zeros((384,384),np.uint8)
 if comp['parts']:
  pix,size,box,_=r.compose_indices(raw,count,comp,allowed_cluts={0,1,2,3})
  assert -160<=box[0]<=box[2]<=224 and -160<=box[1]<=box[3]<=224
  out[160+box[1]:160+box[3],160+box[0]:160+box[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
 return out

def composite(layers,pal,mask,arm):
 out=np.zeros((384,384),np.uint32)
 for bit,cb in((0,0),(8,8),(1,5),(4,7),(2,6)):
  if bit and not mask&bit:continue
  a=layers[cb];offset=0 if cb==0 else 32 if cb==7 and arm==2 else 16
  colors=np.array(pal[offset:offset+16],np.uint32)+1;out[a>0]=colors[a[a>0]]
 return out

def verify(name):
 before=(ROOT/q['sources'][name]).read_bytes();after=(ROOT/q['files'][name]['path']).read_bytes()
 assert r.sha(before)==SOURCES[name] and r.sha(after)==EXPECTED[name]==q['files'][name]['after']
 g,c,p=(r.unique_entry(before,t)for t in(2,3,9));ng,nc,npal=(r.unique_entry(after,t)for t in(2,3,9))
 assert len(before)==len(after)==796672 and p==npal
 assert r.entry_replace(r.entry_replace(after,2,g),3,c)==before
 assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True) and bank_offsets(c)==bank_offsets(nc)
 checked=0;changed=[];encoded_preserved=0
 for bank in range(len(bank_offsets(g,allow_aliases=True))):
  for of in graphics_bank(g,bank,allow_bank_aliases=True)['frames']:
   n=of['index'];a,af=r.native_raw(g,bank,n);b,bf=r.native_raw(ng,bank,n)
   assert af['tile_count']==bf['tile_count']
   if a!=b:changed.append([bank,n]);assert bank==0 and n==141
   if bank!=0 or n!=141:
    assert a==b
    ad=decode_stream(g,af['offset'],af['limit'],af['tile_count']*128)
    bd=decode_stream(ng,bf['offset'],bf['limit'],bf['tile_count']*128)
    assert g[af['offset']:ad.end]==ng[bf['offset']:bd.end];encoded_preserved+=1
   checked+=1
 assert changed==[[0,141]]
 composition_checks=0
 for cb,off in enumerate(bank_offsets(c)):
  count=struct.unpack_from('<I',c,off)[0]>>16
  assert struct.unpack_from('<I',nc,off)[0]>>16==count
  for n in range(count):
   if n==141 and cb in r.PARTS:continue
   assert records(composition_frame(c,cb,n))==records(composition_frame(nc,cb,n));composition_checks+=1
 original141,of=r.native_raw(g,0,141);new141,nf=r.native_raw(ng,0,141);idle,zf=r.native_raw(g,0,0)
 assert nf['tile_count']<=32
 oldbase=layer(original141,of['tile_count'],c,0,141)
 yy,xx=np.indices((384,384));outside=(xx<142)|(xx>178);fx=np.where(outside,oldbase,0).astype(np.uint8)
 assert int(np.count_nonzero(fx))==12
 positions=[[int(x-160),int(y-160),int(fx[y,x])]for y,x in np.argwhere(fx>0)]
 layers=0
 for n in range(237):
  if n in r.X_PLACEHOLDERS:continue
  a,af=r.native_raw(g,0,n);b,bf=r.native_raw(ng,0,n)
  for cb in r.PARTS:
   if n==141:
    goal=layer(idle,zf['tile_count'],c,cb,0)
    if cb==0:
     assert not np.any((goal>0)&(fx>0)), 'Spark overlaps idle body'
     goal=np.where(fx,fx,goal)
   else:goal=layer(a,af['tile_count'],c,cb,n)
   assert np.array_equal(layer(b,bf['tile_count'],nc,cb,n),goal);layers+=1
 # Check shared original 141 records themselves, not just their final pixels.
 shared=[]
 for cb in(5,6,7,8):
  oldparts=composition_frame(c,cb,141)['parts'];addresses={pp['record_offset']for pp in oldparts}
  for n in range(237):
   if n==141:continue
   common=addresses&{pp['record_offset']for pp in composition_frame(c,cb,n)['parts']}
   if common:
    for at in common:assert c[at:at+4]==nc[at:at+4]
    shared.append({'bank':cb,'other_frame':n,'shared_records':len(common),'bytes_exact':True})
 if name=='PL02_U.ARC':
  assert nf['tile_count']==17 and zf['tile_count']==15
  offsets=bank_offsets(c)
  for cb in(5,6,7,8):
   at=offsets[cb];assert nc[at+141*4:at+142*4]==c[at:at+4]
  assert any(x['other_frame']==138 for x in shared)
 else:
  assert records(composition_frame(c,0,141))==records(composition_frame(nc,0,141))
  oa=np.frombuffer(indexed_atlas(original141,of['tile_count'])[0],np.uint8).reshape(-1,256)
  na=np.frombuffer(indexed_atlas(new141,nf['tile_count'])[0],np.uint8).reshape(-1,256)
  for pp in composition_frame(c,0,141)['parts']:
   t=pp['tile'];y,x=t//16*16,t%16*16;assert np.array_equal(oa[y:y+16,x:x+16],na[y:y+16,x:x+16])
  assert np.array_equal(oldbase,layer(new141,nf['tile_count'],nc,0,141))
 pal=struct.unpack_from('<64H',p);mask_checks=[]
 base={cb:layer(idle,zf['tile_count'],c,cb,0)for cb in r.PARTS}
 actual={cb:layer(new141,nf['tile_count'],nc,cb,141)for cb in r.PARTS}
 for arm in(1,2):
  for mask in range(16):
   goal=composite(base,pal,mask,arm);observed=composite(actual,pal,mask,arm)
   goal[fx>0]=np.array(pal[:16],np.uint32)[fx[fx>0]]+1
   assert np.array_equal(goal,observed)
   mask_checks.append({'arm':arm,'mask':mask,'equals_idle_plus12_sparks':True})
 atlas=np.frombuffer(indexed_atlas(new141,nf['tile_count'])[0],np.uint8).reshape(-1,256);boundaries=[]
 for cb in(r.PARTS if name=='PL02_U.ARC' else(5,6,7,8)):
  for part in composition_frame(nc,cb,141)['parts']:
   t=part['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
   assert t%16!=0 or not np.any(tile[:,0]);assert not part['flip_y']or t//16%16!=0 or not np.any(tile[0])
   boundaries.append({'parts_bank':cb,'tile':t,'flip_y':part['flip_y']})
 return {'passed':True,'input_sha256':r.sha(before),'after_sha256':r.sha(after),'decoded_refs':checked,'nonselected_encoded_refs_exact':encoded_preserved,
  'parts_compositions_checked':composition_checks,'display_layers_checked':layers,'changed_raw_refs':changed,'frame141_tiles':nf['tile_count'],
  'spark_world_indices_exact':positions,'shared_141_records_preserved':shared,'mask_checks':mask_checks,'new_gpu_boundary_parts':boundaries,
  'all_other_refs_including0_126through140_138_142_exact':True,'palette_audio_other_entries_exact':True,
  'PL00_base141_raw_tiles_parts_and_display_exact':name=='PL00_U.ARC','scope':'수용된 PL00 기본141의 idle+12잔광 규칙 통일; 원작별도포즈 복구 주장이 아님.',
  'runtime_verified':False}

report={'passed':True,'assets':{n:verify(n)for n in EXPECTED},'game_bin_state_or_pointer_modified':False}
r.write(Path(__file__).with_name('arrival141_final_independent.json'),report)
print(json.dumps({'passed':True,'resources':{n:{'decoded':v['decoded_refs'],'layers':v['display_layers_checked'],'masks':len(v['mask_checks'])}for n,v in report['assets'].items()}}))
