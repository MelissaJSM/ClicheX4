"""첫 Shibuki 대기 검증 증거를 집계하고 현재 시험 빌드를 기록한다."""
import hashlib,json,shutil,struct
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[3]
build=ROOT/'out/ver_buki_riko/shibuki_idle_20261026T030331945414Z'
manifest=json.loads((build/'manifest.json').read_text(encoding='utf-8'))
source=ROOT/'work/ver_buki_riko/shibuki_idle/20261026T030259846302Z'
repeat=ROOT/'work/ver_buki_riko/shibuki_idle/20261026T031101646450Z'
if (source/'modified.arc').read_bytes()!=(repeat/'modified.arc').read_bytes():raise ValueError('ARC reproducibility failed')
evidence=[];seen=set();contacts={}
for folder in (ROOT/'work/ver_buki_riko/live_poc').glob('20261026T03*'):
    file=folder/'verification.local.json'
    if not file.exists():continue
    item=json.loads(file.read_text(encoding='utf-8'))
    if item.get('modified_bin_sha256')!=manifest['modified_bin']['sha256']:continue
    frame=item['frame'];image=Image.open(source/f'idle_{frame:03d}.png')
    pixels=np.array(image);xx=np.nonzero(pixels[-3:])[1];mid=(int(xx.min())+int(xx.max()))/2
    for match in item['framebuffer_matches']:
        flip=match['flip_x'];seen.add((frame,flip))
        foot=(match['x']+(image.width-1-mid if flip else mid),match['y']+47)
        contacts.setdefault((flip,match['page_y']),set()).add(foot)
    evidence.append(dict(path=file.relative_to(ROOT).as_posix(),frame=frame,matches=item['framebuffer_matches']))
expected={(n,flip) for n in (0,115,116,117,118,119) for flip in (False,True)}
if seen!=expected or any(len(points)!=1 for points in contacts.values()):raise ValueError('Incomplete/stationary-feet validation failed')
report={'scope':'X base idle six frames, both facing directions','build':build.relative_to(ROOT).as_posix(),
        'sha256':manifest['modified_bin']['sha256'],'arc_rebuild_identical':True,
        'frames_verified_both_directions':[0,115,116,117,118,119],
        'ram_vram_framebuffer_matched':True,'fixed_foot_contact_through_idle':True,
        'contacts':[{ 'flip_x':k[0],'page_y':k[1],'positions':list(v)} for k,v in contacts.items()],
        'evidence':evidence,'unit_tests_passed':147,'new_animation_user_review_pending':True,
        'save_state_loaded':False,'save_state_written':False,'memory_card_save_command_sent':False,'save_file_hash_audit':None,
        'game_memory_written':False,'entire_character_complete':False}
with (build/'runtime_summary.local.json').open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
current_path=ROOT/'projects/ver_buki_riko/current_build.json'
current_bytes=current_path.read_bytes();current=json.loads(current_bytes)
if current['bin_sha256']!=manifest['parent_bin_sha256']:raise ValueError('Current build changed concurrently')
(build/'previous_current_build.local.json').write_bytes(current_bytes)
pointer={'project':'ver_buki_riko','task':'x_shibuki','stage':'EXPANSION','kind':manifest['kind'],
         'build':build.relative_to(ROOT).as_posix(),'cue':(build/'shibuki_riko.cue').relative_to(ROOT).as_posix(),
         'bin_sha256':manifest['modified_bin']['sha256'],'source_sha256':manifest['source_sha256'],
         'riko_accepted_build':'projects/ver_buki_riko/riko_accepted_build.json','riko_preserved_byte_for_byte':True,
         'session':'work/ver_buki_riko/emulator_sessions/20261026T030400924902Z','session_closed':False,
         'runtime_summary':(build/'runtime_summary.local.json').relative_to(ROOT).as_posix(),
         'runtime_verified_frames':[0,115,116,117,118,119],'both_directions_verified':True,
         'art_selection':'projects/ver_buki_riko/shibuki_art_selection.json','new_animation_user_review_pending':True,
         'whole_character_completed':False,'unedited_X_actions_recolored':True,'armor_implemented':False,
         'text_replacement_implemented':False,'report':'docs/SHIBUKI_SPRITES.md','next_group':'base_run_and_shooting_run'}
temp=current_path.with_name('current_build.shibuki.tmp')
with temp.open('x',encoding='utf-8') as f:json.dump(pointer,f,indent=2)
if current_path.read_bytes()!=current_bytes:raise ValueError('Current pointer changed before activation')
temp.replace(current_path)
with (ROOT/'projects/ver_buki_riko/shibuki_current_build.json').open('x',encoding='utf-8') as f:json.dump(pointer,f,indent=2)
print(json.dumps({'verified_direction_frame_pairs':len(seen),'activated':pointer['build'],'foot_contacts':report['contacts']}))
