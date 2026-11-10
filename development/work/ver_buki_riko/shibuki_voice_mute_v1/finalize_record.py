"""Publish the verified local voice-mute build pointer; no game input."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
D=ROOT/'work/ver_buki_riko/shibuki_voice_mute_v1'
B=ROOT/'out/ver_buki_riko/shibuki_voice_mute_20261028T064914983985Z'
def read(p):return json.loads(p.read_text('utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
m=read(B/'manifest.json');assert digest(B/'shibuki_riko.bin')==m['modified_bin']['sha256']
protected=[]
for item in read(ROOT/'work/ver_buki_riko/korean_v1/typography_final_preservation.json')['files']:
    after=digest(ROOT/item['path']);protected.append({'path':item['path'],'before':item['sha256'],'after':after,'unchanged':after==item['sha256']})
save(D/'final_preservation.json',{'files':protected,'save_state_keys_sent':False,'registry_changed':False})
record={'build':str(B.relative_to(ROOT)),'cue':str((B/'shibuki_riko.cue').relative_to(ROOT)),
    'bin_sha256':m['modified_bin']['sha256'],'source_sha256':m['source_sha256'],
    'parent_sha256':m['parent_bin_sha256'],'stage':'VOICE_MUTED_USER_REVIEW',
    'recipe':m['recipe'],'voice_mode':'muted','commands_per_archive':13,'unique_waves_per_archive':12,
    'decoded_pcm_zero':True,'nonvoice_payload_preserved':True,'unit_tests_passed':13,'negative_cases_passed':6,
    'full_disc_sectors_compared':251793,'changed_sectors':56,'runtime_audio_verified':False,
    'full_game_runtime_verified':False,'user_accepted':False,'user_test_pending':True,
    'boot_verified':True,'boot_verification_scope':'새 BIN의 메모리카드 데이터 불러오기 화면을 캡처·열람',
    'session':'work/ver_buki_riko/emulator_sessions/20261028T065025359183Z',
    'capture':'work/ver_buki_riko/emulator_sessions/20261028T065025359183Z/20261028T065232588456Z.png',
    'protected_unchanged':sum(x['unchanged'] for x in protected),'protected_count':len(protected),
    'report':'docs/SHIBUKI_VOICE_MUTE.md'}
save(D/'completion.json',record)
save(ROOT/'projects/ver_buki_riko/shibuki_voice_candidate.json',record)
p=ROOT/'projects/ver_buki_riko/project.json';v=read(p)
v.update(latest_integrated_build=record['build'],latest_integrated_bin_sha256=record['bin_sha256'],
         active_task='x_shibuki_audio',active_substage=record['stage'],shibuki_voice_candidate='projects/ver_buki_riko/shibuki_voice_candidate.json')
save(p,v)
m.update(boot_verified=True,boot_capture=record['capture'],session=record['session'],
    runtime_audio_verified=False,full_game_runtime_verified=False,unit_tests_passed=13,
    negative_cases_passed=6,completion_record=str((D/'completion.json').relative_to(ROOT)))
save(B/'manifest.json',m)
print(json.dumps({'build':record['build'],'protected_unchanged':record['protected_unchanged'],'protected_count':len(protected),'boot_verified':True,'audio_playtest_pending':True}))
