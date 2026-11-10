"""Stage four new wall/air keys and their exact displayed aliases in bounded banks."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_rear_continuation as shared
core=shared.core
core.P=D/'rin_extension/prepared_victory_details_v1/PL01_U.ARC';core.SHA='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e'
core.ART=D/'rin_extension/wall_followup_registered_v2';core.OUT=D/'rin_extension/prepared_wall_followup_v2'
core.EXPECTED_SHA={'b0_034':'5f057fb3bce32cb93edcd69c073b3e845498b4d739a4978a8b23aa65a73dc2be','b0_036':'17be78053f6c40a74fd6630a2390d0eb7bc22fa77dbb76f80f3d23f825da3e67','b0_038':'5a40cc92b8c9bcc92c4af99052f6900f96bdbd3296dc7df1929cecd4f9de94ce','b0_041':'bb98a83158a70e0b5121a1145af19ba32ced3014b8f6e8c0d76158547a3fdb6a'}
core.MAP={(0,n):(f'b0_{41 if n in(42,43)else n:03}',False)for n in(34,36,38,41,42,43)};shared.CACHE=D/'rin_extension/wall_followup_pack_cache_v1'
def pack(c,b,n,raw,count,target):
 try:
  #42's ninth record already duplicated its eighth. Preserve that draw multiplicity
  # while using the same 8-part image as41/43; all three keep their own part counts.
  if n in(42,43):
   oldrec=core.engine.records(c,b*5,n);nr,rec,method=shared.pack(c,b,41,raw,count,target)
   if len(oldrec)==len(rec)+4:
    core.engine.native.need(oldrec[-8:-4]==oldrec[-4:],'Unexpected extra alias record')
    rec+=rec[-4:]
   core.engine.native.need(len(oldrec)==len(rec),'Unexpected alias part count')
   return nr,rec,{'type':'canonical_exact_alias_existing_duplicate_record','master':41,'original_part_count':len(oldrec)//4,'duplicate_last_record_preserved':n==42,'canonical_method':method,'hidden_global_cleanup':False}
  return shared.pack(c,b,n,raw,count,target)
 except ValueError as exc:
  if 'fixed-tile window solution' not in str(exc) and 'Uncovered authored pixels' not in str(exc):raise
  from scripts.solve_sprite_cover import cover
  native=core.engine.native;cp=native.composition_frame(c,b*5,n);ids=[t for t in range(count)if t%16!=0]
  layout=cover(target>0,min(len(ids),len(cp['parts'])),20);native.need(layout['fits'],'Cannot cover fixed-origin new art without page-edge tiles')
  rec=b''.join(bytes([0,t,(x-160)&255,(y-160)&255])for t,(x,y)in zip(ids,layout['rects']))
  while len(rec)<len(cp['parts'])*4:rec+=rec[-4:]
  local=bytearray(c)
  for p,j in zip(cp['parts'],range(0,len(rec),4)):local[p['record_offset']:p['record_offset']+4]=rec[j:j+4]
  nc=native.composition_frame(local,b*5,n);_,size,bb,_=native.compose_indices(raw,count,nc);crop=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
  nr=native.packer.edit_visible_set(raw,count,[(nc,crop.tobytes(),size)])
  # Tile0 and every unreferenced texel retain the old raw value: no hidden cleanup.
  before,_,_=native.indexed_atlas(raw,count);after,_,_=native.indexed_atlas(nr,count)
  aa=np.frombuffer(before,np.uint8).reshape(-1,256);zz=np.frombuffer(after,np.uint8).reshape(-1,256)
  for t in set(range(count))-set(ids[:len(layout['rects'])]):
   y,x=t//16*16,t%16*16;native.need(np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16]),'Unused tile changed')
  return nr,rec,{'type':'visible_rectangles_same_tile_and_part_counts','rectangles':layout['rects'],'tiles_used':ids[:len(layout['rects'])],'page_edge_tiles_unused':True,'hidden_global_cleanup':False,'art_translation':[0,0]}
core.pack=pack
def main():
 assert not core.OUT.exists(),'Choose a new candidate output'
 assert hashlib.sha256((D/'rin_extension/wall_followup01/generated.png').read_bytes()).hexdigest()=='bf9d790730fe4b6041a18f8b17e3d4afdd80f635c437a3ffc8bc7745806e8e3f'
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'));j['cumulative_main_refs']=97;j['previous_frozen_art_refs']=91;j['verification'].pop('previous42_exact',None);j['verification']['previous91_exact']=True
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'victory91_preserved_from_parent':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((core.ART/'registration.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'공중/벽 연결34/36/38/41 새4키와 원래 전체 표시가 같은42/43. 이전91·효과·소리·정적몸체 보존. 손목 국소등록은 아직 루트 검토 대기.','ready_for_checkpoint_integration':False})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8');j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from91']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':97}))
if __name__=='__main__':main()
