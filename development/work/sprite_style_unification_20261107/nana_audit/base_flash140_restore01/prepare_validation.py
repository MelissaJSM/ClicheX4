"""140의 작은 후속후보 입력잠금/원코드계획/현재자료를 보존한다."""
from pack_flash import *
FINAL='2822a9387a69119e6a3f6ba0f3cc830676280309b139494221940e0e9a005c59'
def validate(parent,read=lambda f:f.read_bytes()):
 need(sha(parent)==BEFORE,'부모');p=D/'packed_flash_candidate_v1';m=json.loads(read(p/'INPUT_FROZEN.json'));need(m['candidate_sha256']==FINAL and m['parent_sha256']==BEFORE and m['refs']==[140],'잠금범위')
 for q in m['files']:
  f=(ROOT/q['path']).resolve();need(f.is_relative_to(ROOT),'입력경로');need(sha(read(f))==q['sha256'],'입력해시 '+q['path'])
 need(sha(read(p/'PL00_U.ARC'))==FINAL,'후보해시');return m
def main():
 p=D/'packed_flash_candidate_v1';need(digest(p/'PL00_U.ARC')==FINAL and not(p/'INPUT_FROZEN.json').exists(),'최종신규잠금');source=W/'zero_audit/nana_base_effect_callers01';files=[P,P.with_name('FROZEN.json'),D/'pack_flash.py',Path(__file__).resolve(),D/'read_plan.py',D/'read_plan.json',*[p/f'layer{pb}_140.png'for pb in PBS],N/'native_restore/preview_restore.py',N/'base_run_repaint/pack_cycle.py',*[f for f in source.iterdir()if f.is_file()]]
 files += [ROOT/f for f in('scripts/prepare_shibuki_ultimate_production.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_riko_ui.py','scripts/export_x_consistency.py','src/psx_player.py','src/psx_ui_atlas.py')];files=sorted(set(files));write(p/'INPUT_FROZEN.json',{'candidate_sha256':FINAL,'parent_sha256':BEFORE,'refs':[140],'source_policy':'현재idle의각부분층에서baseidle밖알파72/3/1/73만13색추가.원140본체/46효과불변,노바동결과분리.','files':[{'path':f.relative_to(ROOT).as_posix(),'sha256':digest(f)}for f in files]})
 write(D/'native_components_v1.json',{'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v42/rin_nana.bin','source_sha256':'11bd3ecd39e4456ca21a759304400d61cfe5c0981abed55b93fd0377c3ea18a8','resources':{'PL00_U.ARC':{'path':(p/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':FINAL}},'checkpoint_only':True});write(p/'proposal.json',{'project':'ver_rin_nana','parent_arc_sha256':BEFORE,'files':{'PL00_U.ARC':{'path':(p/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':FINAL,'parent_arc_sha256':BEFORE}},'new_art_source_cells':0,'refs':[140]});print(json.dumps({'lock':digest(p/'INPUT_FROZEN.json'),'inputs':len(files),'candidate':FINAL}))
if __name__=='__main__':main()
