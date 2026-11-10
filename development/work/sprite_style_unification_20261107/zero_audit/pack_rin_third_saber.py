"""Five newly authored poses -> ten exact alias refs on frozen Rin52."""
from pathlib import Path
import sys,json,hashlib,shutil
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_priority_body as core
core.P=D/'rin_extension/prepared_burst_pair_final_v1/PL01_U.ARC'
core.SHA='10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
core.ART=D/'rin_extension/third_saber_registered_v2'
core.OUT=D/'rin_extension/prepared_third_saber_v1'
core.EXPECTED_SHA={
 'b0_109':'bec5ba4131dc13d96bb66854f71a6af915558bf28b77b545126392cd81779b0e',
 'b0_111':'da5a10d2cb51f3553a842160c5f62f378fc7c885a67a6dfdb16ac898c9e62e35',
 'b0_113':'d19469a045f71fe1490077fb9549262a2843ddbfcc0c9d5f8a31a0328111de58',
 'b0_115':'b7d06ea7594704adcf816b0e49df34f5e0cb56554ccee2277715163f74cb6a43',
 'b0_121':'3391032a953156736b5481eb010f92d532911561ee2e401a8ec0d58b496a3f0d'}
core.MAP={(0,n):(f'b0_{master:03}',False)for master,refs in [(109,[109]),(111,[111]),(113,[113]),(115,[115,117,119]),(121,[121,123,125,127])]for n in refs}

def main():
 assert not core.OUT.exists(),'Use a new candidate directory'
 registration=json.loads((core.ART/'registration.json').read_text('utf8'))
 for r in registration['records']:
  p=core.ROOT/r['generated'];assert hashlib.sha256(p.read_bytes()).hexdigest()==r['generated_sha256']
  assert r['after_sha256']==core.EXPECTED_SHA[r['key']]
 core.main()
 p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'))
 j['cumulative_main_refs']=62;j['previous_frozen_art_refs']=52
 j['verification'].pop('previous42_exact',None);j['verification']['previous52_exact']=True
 j['static_burst24_sync_required']=False;j['static_burst23_sync_required']=False;j['victory5_included']=True
 j['user_accepted']=False;j['root_review_only']=True;j['root_review_pending']=True
 j['registration']=str((core.ART/'registration.json').relative_to(core.ROOT))
 j['native_master_sha256']=core.EXPECTED_SHA
 j['scope']='새 3타 원화5키를 정확한 전신 공유10참조에 등록. 기존52와 검기·타이밍·음향은 보존.'
 src=core.P.parent;recipe=json.loads((src/'static_effects.json').read_text('utf8'))
 recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in['palette.bin','effect_23.png','effect_24.png']:shutil.copyfile(src/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j['static_effect_recipe']=str(rp.relative_to(core.ROOT));j['static_effect_recipe_sha256']=hashlib.sha256(rp.read_bytes()).hexdigest()
 j['static_body_patch']={'recipe':j['static_effect_recipe'],'sha256':j['static_effect_recipe_sha256']}
 j['static_body_images_and_texture_unchanged_from52']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':62}))
if __name__=='__main__':main()
