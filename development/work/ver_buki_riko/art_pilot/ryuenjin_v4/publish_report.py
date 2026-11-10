from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def read(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def rel(p):return Path(p).relative_to(ROOT).as_posix()
B=Path(read(D/'builds.json')['build']['output']);H=read(B/'manifest.json')['modified_bin']['sha256'];M=Path(read(D/'master_export.json')['output']);split=Path(read(D/'master_split.json')['output'])
S='work/ver_buki_riko/emulator_sessions/20261025T121654830925Z';R='work/ver_buki_riko/rise_runtime/20261025T121843451304Z/verification.local.json';CS='work/ver_buki_riko/current_build_saves/20261025T122118036242Z'
v=read(ROOT/R);save=read(ROOT/CS/'manifest.local.json');ram=[int(n) for n,r in v['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in r['samples'])]
assert len(ram)==11 and save['bin_sha256']==H and save['full_current_bank1_present']
summary={'build':rel(B),'bin_sha256':H,'session':S,'evidence':R,'ram_vram_palette_frames':ram,'full_screen_frames':v['verified_frames'],'user_accepts_progression':True,'user_report':'이상없다면 다음 작업으로 진행해도 좋다고봐. 아직 남은게 꽤나있던거같은데말야','remaining_visual_note':'Small original transparent fire-edge notch is more visible beside narrow Riko wrist; inspected and retained','current_save':CS,'fresh_card_navigation_observed_by_agent':False,'entry_completed_off_observation':True,'agent_loaded_f1':False,'f3_tested_this_build':False,'next_group':'rakuhouha','process_memory_written':False}
write(D/'runtime_summary.json',summary)
backup=D/'publication_backup';backup.mkdir(exist_ok=False)
for path in ('projects/ver_buki_riko/current_build.json','projects/ver_buki_riko/master_sheet.json','docs/STATUS.md','docs/RIKO_RYUENJIN.md'):shutil.copyfile(ROOT/path,backup/Path(path).name)
p=ROOT/'projects/ver_buki_riko/current_build.json';cur=read(p)
cur.update(kind='riko_wall_spin_ice_rise_turn_grip_bank1_v4',previous_build=cur['build'],previous_bin_sha256=cur['bin_sha256'],previous_pointer_snapshot=rel(backup/'current_build.json'),build=rel(B),cue=rel(B/'riko_motion.cue'),bin_sha256=H,session=S,session_closed=False,runtime_summary=rel(D/'runtime_summary.json'),runtime_verified_frames=v['verified_frames'],rise_ram_vram_verified_frames=ram,rise_full_framebuffer_verified_frames=v['verified_frames'],rise_art_user_review_pending=False,rise_user_accepts_progression=True,bank1_set=rel(D/'recipe.json'),current_build_save=CS,agent_loaded_save_state=False,save_roundtrip=None,riko_reference_count=209,original_saber_effect_references_preserved=83,all_current_frames_preview=rel(M/'riko_master_preview_2x.png'),session_state_at_last_observation='Current complete banks verified; user-assisted unobserved stage entry; F1 saved in pause menu at 726/426',session_state_evidence=CS+'/manifest.local.json',next_task='Rakuhouha103 original body/effect analysis and production; preserve accepted Ryuenjin',report='docs/RIKO_RYUENJIN.md')
cur.pop('pending_build',None);write(p,cur)
p=ROOT/'projects/ver_buki_riko/master_sheet.json';cur=read(p);cur.update(source_build=rel(B),source_bin_sha256=H,directory=rel(M),master=rel(M/'master.local.json'),sheet=rel(M/'riko_master_indexed.png'),preview=rel(M/'riko_master_preview_2x.png'),roundtrip=rel(split/'validation.local.json'),riko_references=209,next_group='rakuhouha',report='docs/RIKO_RYUENJIN.md',rise_art_review_pending=False);write(p,cur)
p=ROOT/'docs/RIKO_RYUENJIN.md';s=p.read_text('utf8').replace('최신 손잡이 수정안의 최종 사용자 평가는 아직 없다.','사용자는 작은 빈 부분을 언급하면서 다음 작업 진행을 허용했다. 확대 대조 후 현재 수정본을 유지한다.');s=s[:s.index('## 실행 검증')]+f'''## 실행 검증과 수용

`{R}`:11몸 모두 RAM·VRAM·팔레트 일치. 자동 전체 불투명 픽셀 화면 일치는160 한 프레임이며 나머지10몸은 미확인이다. 같은 캡처를 확대하여 손잡이·화염 연결을 육안 확인했다. 효과가 몸을 가리는 경우를 포함하며 자동 전체 화면11/11 통과로 보고하지 않는다.

`ryuenjin_v4/fire_hole_comparison.png`는 실제 화염 팔레트로 원본과 Riko를 합성한 윗2행 및 실제 캡처 아랫행을 구분한다. 원본 화염의 투명한 아랫부분이 Riko의 가느다란 손목과 짙은 손잡이 근처에서 더 도드라져 보이는 것으로 판단했다. 효과 원본 바이트는 그대로이며 손잡이의 연결은 확인됐다. 사용자는 “약간 불꽃에 빈곳이 살짝보이긴하는데.. 넘어가도되긴할정도긴한데 너가한번봐봐”, 이후 “이상없다면 다음 작업으로 진행해도 좋다고봐. 아직 남은게 꽤나있던거같은데말야”라고 했다. 현 수정본을 유지하고 낙봉파로 진행한다. 미세한 홈을 없앴다고 주장하지 않는다.

세션 `{S}`. 에이전트가 새 BIN을 시작했고 사용자가 관찰 밖에서 스테이지 진입을 완료했다. 에이전트가 카드 로드 전 과정을 관찰한 것은 아니다. 현재 bank0/bank1 전체가 새 빌드와 일치함을 확인했다. 원본과 구버전 bank1은 현재 RAM에 없었다.

작업용F1 `{CS}`,SHA-256 `{save['state_sha256']}`. 제로·8보스0xFF·HP48·Jungle726/426, 메뉴 저장. F1 내부 새 bank0/bank1 전체 검증, 이전 F1 백업, 카드 해시 유지 완료. 동일 빌드F3 재시험은 미실행이다. 원본 사용자 저장을 덮어쓰지 않았다.

79변경 섹터 EDC/ECC·반복 BIN 동일·209 PNG/ARC 마스터 왕복 통과. 모든 지형·좌우·피격·취소 조합과 다른 미제작 기술은 미완료다.
''';p.write_text(s,'utf8')
(ROOT/'docs/STATUS.md').write_text(f'''# 프로젝트 상태

2026-10-25 KST. **ZERO_PRODUCTION — 용염인 회전·손잡이 정렬 수용, 다음 낙봉파 제작.** 활성 `ver_buki_riko/zero_riko`, PS1 미국판. 회전 베기 v4·빙열참도 이전 사용자 수용 상태다.

현재 CUE `{rel(B/'riko_motion.cue')}`, BIN SHA-256 `{H}`. 몸을 돌려 등을 보이는 용염인과 원본 화염 접점에 맞춘 팔·손잡이를 적용했다. 작은 원본 화염의 투명 영역은 확대 검토 후 유지한다. 사용자가 다음 작업 진행을 허용했다. [용염인 상세](RIKO_RYUENJIN.md).

누적209몸/섬광·83원본 효과 참조. 빙열참 채택본의276 PNG 보존.105검사·반복 BIN 동일·79섹터 EDC/ECC·209 PNG/ARC 왕복 통과. 용염인11몸 RAM/VRAM/팔레트 일치, 자동 전체 화면은160만 통과했다. 원본 효과·시간표·판정·EXE·배치는 유지했다.

마스터 `{rel(M)}`. 현재 세션 `{S}`, 작업용F1 `{CS}`, 상태 SHA-256 `{save['state_sha256']}`. 두 은행 전체를 확인했고 제로·8보스·HP48·Jungle726/426 메뉴 저장이다. 사용자의 스테이지 진입 조작은 관찰 밖이었다. 이번F3 재시험은 미실행이다. 이전F1·카드·원본 보존.

## 다음 작업과 범위

낙봉파103의 원본 동작·공유 몸·별도 탄/화면 효과를 확인한 뒤 필요한 Riko 몸을 제작한다. 용염인·회전 베기·빙열참의 승인 체격/도트와 원본 로직을 유지한다. 낙봉파·뇌신격·질풍아 및 기절/사망·사다리/벽 일부 전체 화면·모든 지형/피격/취소 조합은 미완료다. Buki/Rin/Nana·아머로 확대하지 않는다.

원본 미국판 `SLUS_005.61`,592217136 bytes,SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 설정화 SHA-256 `0537f596cf21b97916b1b59197890fc15a4460fd36026f560b817da471258796`. 기존 미국판·Riko·같은 길이 그래픽 승인 범위를 따른다.

[전체 특수기술](RIKO_SPECIAL_TECHNIQUES.md),[명령](COMMANDS.md),[용량 정리·복원](STORAGE_MAINTENANCE.md). 이전 상태/포인터는 `{rel(backup)}`에 보존했다.
''','utf8')
def prepend(name,text):
 p=ROOT/'docs'/name;a,b=p.read_text('utf8').split('\n',1);p.write_text(a+'\n\n'+text+'\n'+b.lstrip('\n'),'utf8')
prepend('DECISIONS.md','## 2026-10-25 — 용염인 회전·접점 수정 채택과 낙봉파 진행\n\n정면 어퍼컷을 폐기하고 뒤를 보며 올리는 자세로 수정했다. 손잡이와 원본 화염 접점을8몸에서 정렬했다. 사용자는 작은 빈 부분을 언급하면서 다음 작업 진행을 허용했다. 원본 불꽃 아랫부분과 손목 주변 홈은 확대 비교 후 유지하고 낙봉파103으로 진행한다. 승인 범위는 기존 미국판·Riko·같은 길이 그래픽이다. 효과/로직/시간표 변경은 포함하지 않는다. [근거](RIKO_RYUENJIN.md).\n')
prepend('TEST_RESULTS.md','## 2026-10-25 — 용염인 회전과 화염 접점\n\n105검사,72원본참조 무변경 왕복,빙열참276 PNG 보존,209 PNG/ARC 왕복,반복 BIN 동일,79섹터 EDC/ECC 통과.11몸 RAM/VRAM/팔레트 일치,자동 전체 화면160만 통과.8몸 손잡이 끝과 원본 효과 픽셀은 겹치거나8방향 인접. 작은 투명 홈은 남아 있으며 확대 검토 후 사용자 진행 허용에 따라 유지했다. 새F1 두 은행/이전F1백업/카드유지 검증,F3재시험 미실행. [상세](RIKO_RYUENJIN.md).\n')
prepend('ART_DIRECTION.md','**2026-10-25 용염인 채택:** 정면 어퍼컷을 폐기하고 상승148/150/152/154에서 기존23×19 뒷머리와 등·골반 회전을 사용한다. 기존 체격을 유지하며 손잡이를 화염 접점에 등록한다. 회수156/158도 짧은 손잡이를 쥐며 원본 효과에 연결한다. 작은 원본 화염 투명 홈은 검토 후 유지한다. 모든 자세를 정면 머리 하나로 강제하지 않는다. [기준·근거](RIKO_RYUENJIN.md).\n')
prepend('COMMANDS.md','## 2026-10-25 — 용염인 화염 연결\n\n실제로 실행한 명령이다. 빌드 스크립트는 기존 builds.json 덮어쓰기를 거부하며 실행 PID/기준점은 해당 세션 전용이다.\n\n```powershell\npython work/ver_buki_riko/art_pilot/ryuenjin_v4/check_contacts.py\npython work/ver_buki_riko/art_pilot/ryuenjin_v4/build_and_verify.py\npython work/ver_buki_riko/art_pilot/ryuenjin_v4/audit.py\npython scripts/capture_jump_cycle.py --build out/ver_buki_riko/riko_bank1_20261025T121626756176Z --baseline work/ver_buki_riko/live_poc/20261025T121829433271Z/bank_baseline.local.json --rise --observe\npython work/ver_buki_riko/art_pilot/ryuenjin_v4/inspect_fire_holes.py\n```\n')
p=ROOT/'docs/RIKO_SPECIAL_TECHNIQUES.md';s=p.read_text('utf8');lines=s.splitlines();lines[2]='**최신:** 회전 베기 v4·빙열참·용염인 회전/손잡이 수정본은 사용자 진행 허용 상태다. 용염인11몸 RAM/VRAM/팔레트·160 전체 화면·화염 접점을 확인했다([보고서](RIKO_RYUENJIN.md)). 다음은 낙봉파103이다. 나머지 특수기술 완성이 아니다.';s='\n'.join(lines)+'\n';s=s.replace('몸16과 공유88/96/99 후보 제작. 원래 동작16몸·무기parts6 실기 식별, 새 Riko 후보 실기 대기','몸16/공유섬광 제작,16몸 RAM/VRAM/팔레트 일치·사용자 실기 수용. 자동 전체 화면 미확인').replace('몸11·효과8 추출. 별도 불꽃 오브젝트 유지·검증 필요','11몸 적용·효과8/별도 잔불 보존.11몸 RAM/VRAM·160 화면·손잡이 접점 확인, 사용자 진행 허용').replace('회전 베기 v4 수용 후 빙열참97/98과 공유 회수 그림을 진행 중이다.','회전 베기·빙열참·용염인 수용 후 낙봉파103을 진행한다.');p.write_text(s,'utf8')
print(json.dumps(summary,ensure_ascii=False))
