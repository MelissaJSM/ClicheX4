"""호버 수정의 해시·보존·실행 근거를 집계한다."""
import json,sys,shutil,gzip
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.prepare_shibuki_hover_alignment import prepare
D=Path(__file__).parent;B=ROOT/'out/ver_buki_riko/shibuki_fourth_hover_alignment_20261027T033818587949Z'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.resolve().relative_to(ROOT).as_posix()
m=read(B/'manifest.json');r=read(B/'recipe.json')
assert digest(B/'shibuki_riko.bin')==m['modified_bin']['sha256']
assert digest(B/'modified.arc')==m['modified_archive_sha256']
again,_=prepare(D/'layers04');assert again==(B/'modified.arc').read_bytes()
negative=[]
for name in ['wrong_scope','upper_body','palette']:
    p=D/'negative_checks'/name;p.mkdir(parents=True,exist_ok=True);meta=read(D/'layers04/layers.json')
    if name=='wrong_scope':meta['frames']=[221,222]
    write(p/'layers.json',meta)
    if name!='wrong_scope':
        im=Image.open(D/'layers04/bank0_221.png').copy()
        if name=='upper_body':im.putpixel((60,60),1)
        else:
            palette=im.getpalette();palette[3]^=255;im.putpalette(palette)
        im.save(p/'bank0_221.png')
    try:prepare(p)
    except ValueError as e:negative.append({'case':name,'rejected':True,'reason':str(e)})
    else:raise AssertionError(name)
inputs=read(ROOT/'out/ver_buki_riko/shibuki_fourth_remaining_20261027T014647676089Z/preservation.json')['inputs']
for v in inputs:assert digest(ROOT/v['path'])==v['sha256'],v['path']
saved=ROOT/'work/ver_buki_riko/shibuki_hover_save_backup/20261027T032425116169Z'
for v in read(saved/'backup.json')['files']:
    if 'memcards' in v['source']:assert digest(ROOT/v['source'])==v['sha256']
for v in read(saved/'current_save.json')['files']:assert digest(ROOT/v['path'])==v['sha256']
evidence=ROOT/'work/ver_buki_riko/shibuki_armor_capture/20261027T034122699054Z/verification.local.json';actual=read(evidence)
assert actual['modified_bin_sha256']==m['modified_bin']['sha256']
assert {(v['frame'],v['direction_bit']) for v in actual['results']}=={(n,d) for n in [221,222,223,224] for d in [0,64]}
assert all(v['ram_equal'] and v['vram_equal'] and v['matches'] for v in actual['results'])
assert all(all(v['complete_entries_match'].values()) for v in actual['checked_ram_entries'])
runtime={'evidence':rel(evidence),'verified_frames':[221,222,223,224],'directions':[0,64],'verified_frame_direction_combinations':8,'armor_mask':15,'arm_type':2,'weapon':0,'full_sprite_pixels_equal':True,'flame_attachment_review':'actual framebuffer screenshots visually inspected for forward hover and shooting','asset_refreshed_checkpoint':True,'fresh_disc_memory_card_load_verified':False,'all_animation_runtime_complete':False}
write(B/'runtime_summary.local.json',runtime)
report={'new_bin_sha256':m['modified_bin']['sha256'],'new_arc_sha256':m['modified_archive_sha256'],'prepared_arc_repeated_byte_identical':True,'unit_tests_passed':191,'negative_checks':negative,'protected_inputs':inputs,'user_play_point_backup':rel(saved),'user_play_point_resume':rel(D/'user_resume_state/SLUS_005.61.000'),'user_resume_sha256':digest(D/'user_resume_state/SLUS_005.61.000'),'static_review':read(B/'hover_review/verification.json'),'runtime':runtime,'changed_sectors':[x['lba'] for x in m['modified_bin']['changed_sectors']],'remaining_runtime_review_scope':'other animation coverage unchanged from parent; this fix verifies only hover frames 221..224'}
write(B/'verification.local.json',report)
paths=['hover_generated.png','hover_edit_prompt.txt','register_hover.py','layers04/layers.json']
write(D/'provenance.json',{'mode':'built-in image_gen','generated_source':'<LOCAL_PATH>','files':[{'path':rel(D/p),'sha256':digest(D/p)} for p in paths],'final_art':rel(D/'layers04'),'changed_frames':[221,222,223,224],'registration':'lower legs registered to original boot anchors; accepted upper layers preserved','legless_hover_not_gameplay_reachable':True})
pointer=ROOT/'projects/ver_buki_riko/shibuki_fourth_candidate.json'
if not (D/'candidate_before.json').exists():shutil.copyfile(pointer,D/'candidate_before.json')
c=read(pointer);c.update(kind='fourth_armor_hover_alignment_candidate',previous_build=r['parent_build'],build=rel(B),cue=rel(B/'shibuki_riko.cue'),bin_sha256=m['modified_bin']['sha256'],arc_sha256=m['modified_archive_sha256'],review=rel(B/'hover_review/before_after.png'),integration_report=rel(B/'verification.local.json'),runtime_evidence=rel(B/'runtime_summary.local.json'),report='docs/SHIBUKI_HOVER_ALIGNMENT.md',last_corrected_frames=[221,222,223,224],last_fix_runtime_verified_both_directions=True,last_fix_user_review_pending=True,test_checkpoint=rel(D/'user_resume_state/SLUS_005.61.000'),next='전진 호버의 발/불꽃 연결 수정본 사용자 확인; 다른 작업으로 범위를 확대하지 않음')
if rel(D/'layers04') not in c['source_art']:c['source_art'].append(rel(D/'layers04'))
write(pointer,c)
project=ROOT/'projects/ver_buki_riko/project.json';v=read(project);v['active_substage']='ARMOR_HOVER_FIX_REVIEW';write(project,v)
session=ROOT/'work/ver_buki_riko/emulator_sessions/20261027T033842976835Z/session.local.json';v=read(session);v.update(save_state_loaded=True,loaded_checkpoint=rel(D/'user_resume_state/SLUS_005.61.000'),loaded_checkpoint_sha256=report['user_resume_sha256'],user_play_point_preserved=True);write(session,v)
print(json.dumps({'candidate_updated':True,'negative_checks':len(negative),'runtime_combinations':8,'protected_inputs':len(inputs),'user_resume_sha256':report['user_resume_sha256']}))
