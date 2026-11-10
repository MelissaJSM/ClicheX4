"""Four refined rising-slash bodies; retain all four shared flame drawings."""
from pathlib import Path
import sys,json,hashlib,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_rear_continuation as shared
core=shared.core
core.P=D/'rin_extension/prepared_rear_continuation2_v1/PL01_U.ARC'
core.SHA='a565e55fb422764432b03fe60d53430fcd5ede2aa95829a655a9c22bcc902c4d'
core.ART=D/'rin_extension/rising_registered_contacts_v1';core.OUT=D/'rin_extension/prepared_rising_rear_v1'
core.EXPECTED_SHA={'b1_148':'eb978411934bd1510b5604c66e1ee8dfc9a853a17649230c0259941b6ae85daf','b1_150':'ee57b33108c7704309b4b3fdeb71faeafe4a05beabec56bdf0eb5b9c614d4c46','b1_152':'90ff8e0d563ade7b5c188f6caf9da17c0e88bd269c8bd0da07700dec48505bfc','b1_154':'182433f88a6937522d6d0cf6d3f3dbfc74f0a84303e061ca574da8f8d89b0a26'}
core.MAP={(1,n):(f'b1_{n:03}',False)for n in(148,150,152,154)}
shared.CACHE=D/'rin_extension/rising_pack_cache_v1'
def pack(c,b,n,raw,count,target):
 if (b,n)!=(1,150):return shared.pack(c,b,n,raw,count,target)
 # Linked rows must move together: an isolated row move opens a 1px seam.
 # This only moves sampling windows; the fixed-origin authored pixels do not move.
 seeded=bytearray(c)
 for p in core.engine.native.composition_frame(c,5,n)['parts']:
  if p['y']>=-24:seeded[p['record_offset']+3]=(p['y']-1)&255
 nr,rec,method=shared.ordinary_pack(bytes(seeded),b,n,raw,count,target)
 return nr,rec,{'type':'linked_sampling_rows','seeded_rows_delta_y':-1,'canonical_method':method,'art_translation':[0,0],'hidden_global_cleanup':False}
core.pack=pack
def main():
 assert not core.OUT.exists(),'Choose a new candidate output'
 assert hashlib.sha256((D/'rin_extension/rising_rear01/generated.png').read_bytes()).hexdigest()=='541661aaad1cae0cb822480e40614a2a6128f6969c482e03b0340f117fcebeb4'
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'))
 j['cumulative_main_refs']=84;j['previous_frozen_art_refs']=80;j['verification'].pop('previous42_exact',None);j['verification']['previous80_exact']=True
 assert set(j['shared_support_refs'])=={'b1_149','b1_151','b1_153','b1_155'}
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((core.ART/'registration.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'용염인 후면148/150/152/154 새4몸체 등록. 공유 불꽃149/151/153/155는 원래 표시 그대로 유지. 기존80·부분VRAM8·음향·시간표 보존.'})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from80']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':84}))
if __name__=='__main__':main()
