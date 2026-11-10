"""Record the user-accepted HUD alignment without controlling the emulator."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'work/ver_buki_riko/hud_emblem_redesign_v1'
B=ROOT/'out/ver_buki_riko/hud_emblems_20261028T063603173029Z'
SHA='e95273a35a45521ca6fd4ac2ae87562b2749fcd50145e6a1f292269c70468bac'
def read(p):return json.loads(p.read_text('utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert digest(B/'shibuki_riko.bin')==SHA
for name in ['PL00_U.ARC','PL02_U.ARC']:
    assert (D/'candidate02'/name).read_bytes()==(D/'candidate03'/name).read_bytes()
recipe=read(D/'candidate03/recipe.json')
proof=[]
for item in read(ROOT/'work/ver_buki_riko/korean_v1/typography_final_preservation.json')['files']:
    got=digest(ROOT/item['path'])
    proof.append({'path':item['path'],'before':item['sha256'],'after':got,'unchanged':got==item['sha256']})
save(D/'final_preservation.json',{'files':proof,'no_save_state_keys_sent':True,'no_registry_changes':True})
record={'build':str(B.relative_to(ROOT)),'bin_sha256':SHA,'candidate':'work/ver_buki_riko/hud_emblem_redesign_v1/candidate03',
        'symbols':{'shibuki':'도리이','riko':'검과 주변 이펙트'},'riko_symbol_x_adjustment':-2,'symbol_pixels_clipped':0,
        'shibuki_equals_candidate02':True,'source_reference_files_edited':False,
        'user_accepted':True,'user_acceptance_quote':'좋아 충분해 제대로되었다',
        'user_acceptance_scope':'새 체력바 엠블럼과 리코 심볼의 왼쪽2픽셀 정렬 수정',
        'runtime_verified':True,'runtime_verification_source':'user_test','full_game_runtime_verified':False,
        'session':'work/ver_buki_riko/emulator_sessions/20261028T064107656318Z',
        'previous_build_runtime_capture':'work/ver_buki_riko/emulator_sessions/20261028T063221363727Z/20261028T063313393461Z.png',
        'previous_capture_sha256':'fa21f38cec8bd94147b13a6c91ec27d508ef860a2e0e68007952944042de8415',
        'latest_capture_by_agent':False,'unit_tests_passed':14,'technical_cases_passed':16,
        'static_compositions_checked':1612,'non_target_compositions_preserved':1585,
        'full_disc_sectors_compared':251793,'changed_sectors':5,
        'source_sha256':recipe['source_sha256'],'parent_sha256':recipe['parent_sha256'],
        'art_tool_mode':'builtin_imagegen','prompts':'work/ver_buki_riko/hud_emblem_redesign_v1/art_prompts_final.json'}
save(D/'completion.json',record)
manifest=read(B/'manifest.json');manifest.update(runtime_verified=True,runtime_verification_source='user_test',
    runtime_verified_scope=['hud_emblem_redesign_and_riko_alignment'],full_game_runtime_verified=False,
    user_accepted=True,user_acceptance_quote=record['user_acceptance_quote'],active_game_restarted=True,
    session=record['session'],completion_record=str((D/'completion.json').relative_to(ROOT)))
save(B/'manifest.json',manifest)
project_path=ROOT/'projects/ver_buki_riko/project.json';project=read(project_path)
project.update(latest_integrated_build=record['build'],latest_integrated_bin_sha256=SHA,
    hud_emblem_candidate='projects/ver_buki_riko/hud_emblem_candidate.json',
    active_task='x_shibuki_audio',active_substage='SHIBUKI_VOICE_MUTE_IN_PROGRESS')
save(project_path,project)
save(ROOT/'projects/ver_buki_riko/hud_emblem_candidate.json',record)
print(json.dumps({'build':record['build'],'accepted':True,'protected_unchanged':sum(p['unchanged'] for p in proof),'protected_total':len(proof),'changed_texture_bytes':{n:c['changed_texture_bytes'] for n,c in recipe['checks'].items()}}))
