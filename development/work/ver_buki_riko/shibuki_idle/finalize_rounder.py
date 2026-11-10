"""둥근 체형의 실제 검증 범위와 사용자 수용을 보존하고 시험 포인터를 갱신한다."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
build=ROOT/'out/ver_buki_riko/shibuki_idle_20261026T044150188556Z'
source=ROOT/'work/ver_buki_riko/shibuki_idle/20261026T044134317838Z'
repeat=ROOT/'work/ver_buki_riko/shibuki_idle/20261026T044300437119Z'
manifest=json.loads((build/'manifest.json').read_text(encoding='utf-8'))
assert (source/'modified.arc').read_bytes()==(repeat/'modified.arc').read_bytes()
frames=[0,115,116,117,118,119];evidence=[];seen=set();contacts={}
for folder in sorted((ROOT/'work/ver_buki_riko/live_poc').glob('20261026T0443*')):
    file=folder/'verification.local.json'
    if not file.exists():continue
    item=json.loads(file.read_text(encoding='utf-8'))
    if item.get('modified_bin_sha256')!=manifest['modified_bin']['sha256']:continue
    n=item['frame'];pic=Image.open(source/f'idle_{n:03d}.png');a=np.array(pic)
    xs=np.nonzero(a[-3:])[1];mid=(int(xs.min())+int(xs.max()))/2
    for match in item['framebuffer_matches']:
        flip=match['flip_x'];seen.add((n,flip))
        foot=(match['x']+(pic.width-1-mid if flip else mid),match['y']+47)
        contacts.setdefault((flip,match['page_y']),set()).add(foot)
    evidence.append({'path':file.relative_to(ROOT).as_posix(),'frame':n,'matches':item['framebuffer_matches']})
assert seen=={(n,True) for n in frames}
assert all(len(v)==1 for v in contacts.values())
report={'build':build.relative_to(ROOT).as_posix(),'sha256':manifest['modified_bin']['sha256'],
        'scope':'six idle frames, right-facing only','frames_verified_right':frames,'frames_verified_left':[],
        'ram_vram_framebuffer_matched':True,'fixed_foot_contact_through_idle':True,
        'contacts':[{'flip_x':k[0],'page_y':k[1],'positions':list(v)} for k,v in contacts.items()],
        'evidence':evidence,'arc_rebuild_identical':True,'unit_tests_passed':147,
        'palette_permutation_rgba_identical':True,'user_style_accepted':True,
        'user_statement':'좋아 분위기 아주 맘에들어 이 기세로 가자',
        'left_runtime_pending_reason':'Emulator process ended before opposite-facing capture completed',
        'save_state_loaded':False,'save_state_written':False,'memory_card_save_command_sent':False,
        'save_file_hash_audit':None,'process_memory_written':False,'entire_character_complete':False}
with (build/'runtime_summary.local.json').open('x',encoding='utf-8') as f:json.dump(report,f,ensure_ascii=False,indent=2)
current_path=ROOT/'projects/ver_buki_riko/current_build.json';old=current_path.read_bytes();current=json.loads(old)
assert current['bin_sha256']=='75193cbc9286c84918a24e2e7468e92010efa8ee591addb52f5615d4b0e73ba3'
(build/'previous_current_build.local.json').write_bytes(old)
selection_path=ROOT/'projects/ver_buki_riko/shibuki_art_selection.json'
(build/'previous_art_selection.local.json').write_bytes(selection_path.read_bytes())
selected=json.loads((ROOT/'projects/ver_buki_riko/shibuki_art_revision.json').read_text(encoding='utf-8'))
selected.update(status='accepted_design_basis',new_design_user_accepted=True,
                previous_selection='out/ver_buki_riko/shibuki_idle_20261026T044150188556Z/previous_art_selection.local.json',
                user_confirmation=report['user_statement'],sequential_base_sprite_production_authorized=True,
                new_animation_art_preapproved=False)
selection_path.write_text(json.dumps(selected,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
current.update(build=build.relative_to(ROOT).as_posix(),cue=(build/'shibuki_riko.cue').relative_to(ROOT).as_posix(),
               bin_sha256=manifest['modified_bin']['sha256'],
               session='work/ver_buki_riko/emulator_sessions/20261026T044221302057Z',session_closed=True,
               runtime_summary=(build/'runtime_summary.local.json').relative_to(ROOT).as_posix(),
               runtime_verified_frames=frames,both_directions_verified=False,
               runtime_verified_directions=['right'],user_style_accepted=True,
               new_animation_user_review_pending=True,next_group='base_run_and_shooting_run')
temp=current_path.with_name('current_build.rounder.tmp')
with temp.open('x',encoding='utf-8') as f:json.dump(current,f,ensure_ascii=False,indent=2)
assert current_path.read_bytes()==old
temp.replace(current_path)
(ROOT/'projects/ver_buki_riko/shibuki_current_build.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'build':current['build'],'direction_frame_pairs':len(seen),'contacts':report['contacts'],'user_style_accepted':True}))
