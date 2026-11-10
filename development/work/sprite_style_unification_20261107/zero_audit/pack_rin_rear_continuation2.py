"""Add the remaining rear four masters as five exact references to Rin75."""
from pathlib import Path
import sys,json,hashlib,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_rear_continuation as shared
core=shared.core
core.P=D/'rin_extension/prepared_rear_continuation_v1/PL01_U.ARC';core.SHA='806b3871055233a5c37c1c2c17685e02aadd07d647be62ea69bf696787f3fbe4'
core.ART=D/'rin_extension/rear_continuation02/native';core.OUT=D/'rin_extension/prepared_rear_continuation2_v1'
core.EXPECTED_SHA={'b0_191':'b49739d80948e2f026f1cb35d3f8cc51f1eab8e05147d86554b169de55fe1e0c','b0_192':'14592ed62637b063f68918d4d1522c341ffead3b2847005dce6062ca0756ba35','b0_194':'58fd05d51a46692c31451a4dfe3e5d442d621405d0be8be5f5d0e21ff7c97378','b0_195':'b0469849ce9192ce6105e9e1bfeb2d75287d0277157eca79377154324d5ff106'}
core.MAP={(0,n):(f'b0_{master:03}',False)for master,refs in [(191,[191]),(192,[192]),(194,[194]),(195,[195,196])]for n in refs}
shared.CACHE=D/'rin_extension/rear2_pack_cache_v1'
def pack(c,b,n,raw,count,target):
 # 196 is the same displayed pose, but has eight parts versus 195's seven.
 # Keep its own disjoint tile owners and let the joint visible writer merge it.
 if (b,n)==(0,196):return shared.ordinary_pack(c,b,n,raw,count,target)
 return shared.pack(c,b,n,raw,count,target)
core.pack=pack
def main():
 assert not core.OUT.exists(),'Choose a new output'
 assert hashlib.sha256((core.ART.parent/'generated.png').read_bytes()).hexdigest()=='cd305386dd977a435b0c6acb4a1e27ec4223ebf0a42523f5d704fd6d039eee0c'
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'))
 j['cumulative_main_refs']=80;j['previous_frozen_art_refs']=75;j['verification'].pop('previous42_exact',None);j['verification']['previous75_exact']=True
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((core.ART/'registration.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'남은 후면191/192/194/195 새원화4키를195/196 동일형을 포함해5참조에 등록했다. 기존75·공유190·부분VRAM8·음향·시간표를 보존한다.'})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8');j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from75']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':80}))
if __name__=='__main__':main()
