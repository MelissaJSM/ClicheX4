"""Stage first-swing detailed masters plus exact alias69; keep external saber data."""
from pathlib import Path
import sys,json,hashlib,shutil,struct
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_wall_followup as previous
core=previous.core
core.P=D/'rin_extension/prepared_hurt_lowhp_v1/PL01_U.ARC';core.SHA='4e18b1cda6731f97272eba361a2ac19df3606f75a19b5352f6025d403196e769'
core.ART=D/'rin_extension/ground_registered_v1';core.OUT=D/'rin_extension/prepared_ground_first_v1'
registration=json.loads((core.ART/'registration.json').read_text('utf8'))
core.EXPECTED_SHA={r['key']:r['output_sha256']for r in registration['records']};assert set(core.EXPECTED_SHA)=={'b0_062','b0_063','b0_065','b0_067'}
core.MAP={(0,n):(f'b0_{67 if n==69 else n:03}',False)for n in(62,63,65,67,69)}
previous.shared.CACHE=D/'rin_extension/ground_first_pack_cache_v1'
JOINT={}
def joint_first(c,raw,count):
 from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
 from scripts.prepare_shibuki_ultimate_production import fast_fit
 import scripts.prepare_shibuki_armor_remaining as remaining
 from scripts.solve_sprite_cover import cover
 from src.psx_player import indexed_atlas,composition_frame
 assert count==32
 arrays=[np.array(Image.open(core.ART/f'b0_{n:03}_indices.png')) for n in(62,63)]
 key=hashlib.sha256(raw+core.engine.records(c,0,62)+core.engine.records(c,0,63)+b''.join(z.tobytes()for z in arrays)).hexdigest()
 if key in JOINT:return JOINT[key]
 cache=D/'rin_extension/ground_first_joint_cache_v1.json'
 if cache.exists():
  j=json.loads(cache.read_text('utf8'))
  if j['key']==key:
   result=(bytes.fromhex(j['raw']),{int(n):bytes.fromhex(r)for n,r in j['records'].items()});JOINT[key]=result;return result
 def fit(mask,limit):
  rr=fast_fit(mask,limit)
  if rr is not None:return rr
  q=cover(mask,limit,20);return q['rects']if q['fits']else None
 remaining.fit=fit
 #Original61 owns0..8; the original saber64 owns28..31. Keep their full
 #raw tiles byte-exact, and repack only62/63's original9..27 tile pool.
 pool=set(range(9,28));assert all(p['tile']not in pool for n in(61,64)for p in composition_frame(c,0,n)['parts'])
 nr,assignments=pack_many_patterns(raw,32,[z[80:240,80:240]for z in arrays],pool,[9,10]);records={}
 for n,parts in zip((62,63),assignments):
  need=len(composition_frame(c,0,n)['parts']);assert len(parts)<=need
  while len(parts)<need:parts.append(parts[-1])
  records[n]=b''.join(struct.pack('<BBbb',f,t,x-80,y-80)for t,x,y,f in parts)
 aa=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);bb=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256)
 for t in set(range(count))-pool:
  y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],bb[y:y+16,x:x+16])
 assert not np.any(bb[16:32,0])
 cache.write_text(json.dumps({'key':key,'raw':nr.hex(),'records':{str(n):r.hex()for n,r in records.items()},'pool':sorted(pool),'preserved_tiles':[0,1,2,3,4,5,6,7,8,28,29,30,31]},indent=2)+'\n','utf8');result=(nr,records);JOINT[key]=result;return result
def pack(c,b,n,raw,count,target):
 if b==0 and n in(61,62,63,64):
  nr,rr=joint_first(c,raw,count)
  return nr,rr.get(n,core.engine.records(c,0,n)),{'type':'same_original_tile_pool_joint62_63','pool':list(range(9,28)),'existing61_and_saber64_raw_tiles_exact':True,'hidden_global_cleanup':False}
 #69 is pixel-identical to67, but has16 rather than21 tiles and10 rather
 #than11 composition records. Reuse authored pixels, not its raw layout.
 if(b,n)==(0,69):
  saved=core.MAP[b,n];core.MAP[b,n]=('b0_069',False)
  try:return previous.pack(c,b,n,raw,count,target)
  finally:core.MAP[b,n]=saved
 return previous.pack(c,b,n,raw,count,target)
core.pack=pack
def main():
 assert not core.OUT.exists(),'Use a separate candidate path'
 assert hashlib.sha256((D/'rin_extension/ground_first01/generated.png').read_bytes()).hexdigest()=='ac417d1d1295943ad845f4b53f5719fca0a0096cb0cfba53afeb1bf376e2af10'
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'));j['cumulative_main_refs']=122;j['previous_frozen_art_refs']=117;j['verification'].pop('previous42_exact',None);j['verification']['previous117_exact']=True
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((core.ART/'registration.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'지상 첫타62/63/65/67 새4키와 완전히 같은69.기존117·순서/시간표·원검기/공유support·부분8·정적몸체 보존.','ready_for_checkpoint_integration':False})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8');j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from117']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':122}))
if __name__=='__main__':main()
