from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def read(p):return json.loads(p.read_text('utf8'))
def save(p,r):p.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n','utf8')
def rel(p):return Path(p).relative_to(ROOT).as_posix()
backup=D/'publication_backup';backup.mkdir(exist_ok=False)
for p in (ROOT/'projects/ver_buki_riko/current_build.json',ROOT/'projects/ver_buki_riko/master_sheet.json',ROOT/'docs/STATUS.md'):
 shutil.copyfile(p,backup/p.name)
build=read(D/'builds.json')['build'];master=read(D/'master_export.json');split=read(D/'master_split.json')
p=ROOT/'projects/ver_buki_riko/current_build.json';c=read(p)
c.update(kind='riko_air_spin_native_body_scale_v3',previous_build=c['build'],previous_bin_sha256=c['bin_sha256'],
 previous_pointer_snapshot=rel(backup/'current_build.json'),build=rel(build['output']),cue=rel(Path(build['output'])/'riko_motion.cue'),bin_sha256=build['sha256'],
 session=None,session_closed=True,runtime_summary=None,runtime_verified_frames=[],riko_reference_count=183,original_saber_effect_references_preserved=72,
 all_current_frames_preview=rel(Path(master['output'])/'riko_master_preview_2x.png'),bank1_set=rel(D/'recipe.json'),
 existing_236_pngs_preserved=True,next_task='Verify body size through idle/jump/spin transitions in native-style revision3',report='docs/RIKO_AIR_SPIN.md',
 current_build_save=None,save_roundtrip=None,session_state_at_last_observation='Revision3 built and statically verified; fresh runtime pending',
 spin_body_size_checks=rel(D/'body_size_checks.json'),spin_style_user_review_pending=True,spin_verified_frames=[],
 spin_previous_candidates_rejected=['air_spin_v1: style','air_spin_v2: body size'],opposite_direction_runtime_required_before_next_group=False)
save(p,c)
p=ROOT/'projects/ver_buki_riko/master_sheet.json';m=read(p);mp=Path(master['output'])
m.update(source_build=c['build'],source_bin_sha256=c['bin_sha256'],directory=rel(mp),master=rel(mp/'master.local.json'),sheet=rel(mp/'riko_master_indexed.png'),
 preview=rel(mp/'riko_master_preview_2x.png'),roundtrip=rel(Path(split['output'])/'validation.local.json'),riko_references=183,
 next_group='air_spin_native_size_runtime',report='docs/RIKO_AIR_SPIN.md',spin_body_size_checks=rel(D/'body_size_checks.json'),spin_art_review_pending=True)
save(p,m)
print(json.dumps({'build':c['build'],'previous':c['previous_build'],'runtime':'pending'}))
