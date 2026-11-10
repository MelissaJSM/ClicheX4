import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
def read(p):return json.loads(p.read_text('utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf-8')
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
b=read(D/'build.json');build=ROOT/b['build'];m=read(build/'manifest.json')
assert digest(build/'shibuki_riko.bin')==b['bin_sha256']
files=[]
for f in read(D/'preservation_before.json')['files']:
    actual=digest(ROOT/f['path']);files.append({**f,'after':actual,'unchanged':actual==f['sha256']})
assert all(f['unchanged'] for f in files)
save(D/'final_preservation.json',{'files':files,'save_state_keys_sent':False,'registry_changed':False})
wheel=read(D/'package_source.json')['wheel'];assert digest(D/wheel['filename'])==wheel['digests']['sha256']
record={**b,'source_sha256':m['source_sha256'],'parent_sha256':m['parent_bin_sha256'],
    'stage':'TITLE_VOICE_USER_ACCEPTED','user_accepted':True,'user_quote':'좀 웃기게 되긴했는데 이정도면 충분하다',
    'acceptance_source':'2026-10-28 새 적용본 실행 중 사용자 청취',
    'runtime_audio_user_verified':True,'automated_runtime_audio_match_verified':False,
    'wave_decode_verified':True,'unit_tests_passed':17,'negative_cases_rejected':4,
    'whole_disc_sectors_compared':251793,'changed_sectors':76,'protected_count':len(files),
    'protected_unchanged':len(files),'session':'work/ver_buki_riko/emulator_sessions/20261028T071415136389Z',
    'report':'docs/CLICHE_TITLE_VOICE.md','next_action':'await_user_task'}
save(D/'completion.json',record);save(ROOT/'projects/ver_buki_riko/title_voice_candidate.json',record)
m.update(user_accepted=True,user_quote=record['user_quote'],runtime_audio_user_verified=True,
    automated_runtime_audio_match_verified=False,session=record['session'],unit_tests_passed=17,
    completion_record='work/ver_buki_riko/title_voice_v1/completion.json')
save(build/'manifest.json',m)
p=ROOT/'projects/ver_buki_riko/project.json';project=read(p)
project.update(latest_integrated_build=b['build'],latest_integrated_bin_sha256=b['bin_sha256'],
    active_task='cliche_title_voice',active_substage='TITLE_VOICE_USER_ACCEPTED',
    title_voice_candidate='projects/ver_buki_riko/title_voice_candidate.json')
save(p,project)
entries={
'docs/STATUS.md':('**2026-10-28 최신 — Cliché X4 타이틀 콜 적용·사용자 수용 완료.** `EXPANSION / cliche_title_voice / TITLE_VOICE_USER_ACCEPTED`. CUE `out/ver_buki_riko/cliche_title_voice_20261028T071319364977Z/shibuki_riko.cue`, BIN SHA-256 `8f130c5e807690e24204cee986717e9f7148e02960bf270359cfe0dae12dc25a`. 사용자 “좀 웃기게 되긴했는데 이정도면 충분하다”를 실제 청취 수용으로 기록한다. 부모는 수용된 X 무음 `ab78f90a…`, 원본은 미국판 `3ceab06a…`. 타이틀 “메가맨 X4”를 새 “Cliché! X four!”로 교체했다. 앞6.24초 효과음·다른 음원·그래픽·한글·EXE/판정·저장 파일은 보존했다.\n\n전체251793섹터 비교에서 XA 음성76섹터만 변경, Form2 EDC·독립 FFmpeg 디코딩·17단위 검사·4거부 사례·BIN 해시 재현·보호13파일 보존 통과. 새 CUE 실행 및 사용자 청취 확인을 완료했다. 자동 루프백 음향 대조와 플레이 전체 전수 검사는 미실행이며 사용자 수용을 확대 해석하지 않는다. 추가 승인 차단 없음, 다음은 사용자 후속 작업 요청 대기. [근거·한계](CLICHE_TITLE_VOICE.md). **아래는 이전 시점 이력이다.**'),
'docs/DECISIONS.md':('## 2026-10-28 — 타이틀 콜 최종 수용\n\n사용자는 새 타이틀 음성 빌드 `8f130c5e…` 실행 후 “좀 웃기게 되긴했는데 이정도면 충분하다”라고 했다. 새 “Cliché! X four!” 음성과 현재 강도·울림을 확정하고 추가 수정/게임 조작을 멈춘다. 앞6.24초 타이틀 효과음, 전투 음향과 다른 자산은 부모 그대로다. 사용자 수용은 직접 청취 근거이며 자동 음질 평가로 대신 기록하지 않는다. [작업 기록](CLICHE_TITLE_VOICE.md).'),
'docs/TEST_RESULTS.md':('**2026-10-28 타이틀 콜 수용 및 X 무음 수용:** X 무음 부모 `ab78f90a…`는 “좋아 이상 없어”로 확인됐다. 타이틀 콜 출력 `8f130c5e…`는 새 음성 “Cliché! X four!”로 변경하고 “좀 웃기게 되긴했는데 이정도면 충분하다”로 수용됐다. 자체/FFmpeg XA389088×2샘플 동일, 압축 SNR39.04dB, 전체251793섹터 중76만 변경 및 Form2 EDC 정상, 다른 채널/자산·13보호파일 보존,17단위/4부정입력 통과. 실제 실행 청취는 사용자 확인이며 자동 루프백 대조는 미실행. [증거](CLICHE_TITLE_VOICE.md).'),
'docs/COMMANDS.md':('## 2026-10-28 — Cliché X4 타이틀 음성\n\n다음 명령을 실제 실행했다. 고정 제작 입력은 `title_voice_v1`에 있으며 게임 출력은 매번 새 타임스탬프 폴더다.\n\n```powershell\nwork/tools/title_voice_env/Scripts/python.exe work/ver_buki_riko/title_voice_v1/generate.py\nwork/tools/voice_env/Scripts/python.exe scripts/prepare_cliche_title_voice.py\nwork/tools/voice_env/Scripts/python.exe -m unittest discover -s tests -p test_psx_xa_audio.py\npython -m unittest tests.test_psx_spu_audio tests.test_riko_voice_patch tests.test_psx_disc tests.test_psx_sector\nwork/tools/voice_env/Scripts/python.exe scripts/build_cliche_title_voice.py\npython scripts/emulator_session.py launch --cue out/ver_buki_riko/cliche_title_voice_20261028T071319364977Z/shibuki_riko.cue --card0 work/ver_buki_riko/korean_v1/runtime_cards_v1/card0.mcr --card1 work/ver_buki_riko/korean_v1/runtime_cards_v1/card1.mcr\n```\n\n재합성은 음색의 비트 동일성을 보장하지 않는다. 수용본의 재현은 고정 `ryan_clean.wav`와 압축/패치 조합을 사용한다. [결과·원본 보호](CLICHE_TITLE_VOICE.md).')}
for path,entry in entries.items():
    p=ROOT/path;s=p.read_text('utf-8');heading,rest=s.split('\n',1)
    p.write_text(heading+'\n\n'+entry+'\n\n'+rest.lstrip(),'utf-8')
print(json.dumps({'build':b['build'],'user_accepted':True,'protected_unchanged':len(files)}))
