from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
def read(p):return json.loads(p.read_text('utf8'))
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
def rel(p):return Path(p).relative_to(ROOT).as_posix()
B=Path(read(D/'builds.json')['build']['output']);H=read(B/'manifest.json')['modified_bin']['sha256']
M=Path(read(D/'master_export.json')['output']);split=Path(read(D/'master_split.json')['output'])
S='work/ver_buki_riko/emulator_sessions/20261025T112051980978Z'
R='work/ver_buki_riko/ice_runtime/20261025T112403672246Z/verification.local.json'
CS='work/ver_buki_riko/current_build_saves/20261025T112700752317Z'
v=read(ROOT/R);save=read(ROOT/CS/'manifest.local.json')
ram=[int(n) for n,r in v['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in r['samples'])]
assert len(ram)==16 and save['bin_sha256']==H and save['full_current_bank1_present']
quote='너무오래걸려서 내가해봤는데 잘되네 다음으로 바로넘어가도될정도야'
summary={'build':rel(B),'bin_sha256':H,'session':S,'evidence':R,'ram_vram_palette_frames':ram,'full_screen_frames':v['verified_frames'],
 'full_screen_unverified':ram,'user_playtest_accepted':True,'user_report':quote,'additional_ice_repetition_stopped_by_user_direction':True,
 'current_save':CS,'save_bank0_equal':True,'save_bank1_present':True,'fresh_card_boot_observed':True,'f3_tested_this_build':False,
 'next_group':'ryuenjin','process_memory_written':False}
write(D/'runtime_summary.json',summary)
backup=D/'publication_backup';backup.mkdir(exist_ok=False)
for p in [ROOT/'projects/ver_buki_riko/current_build.json',ROOT/'projects/ver_buki_riko/master_sheet.json',ROOT/'docs/STATUS.md',ROOT/'docs/RIKO_HYOURETSUZAN.md']:shutil.copyfile(p,backup/p.name)
p=ROOT/'projects/ver_buki_riko/current_build.json';cur=read(p)
cur.update(kind='riko_wall_spin_ice_bank1_v1',previous_build=cur['build'],previous_bin_sha256=cur['bin_sha256'],previous_pointer_snapshot=rel(backup/'current_build.json'),
 build=rel(B),cue=rel(B/'riko_motion.cue'),bin_sha256=H,session=S,session_closed=False,runtime_summary=rel(D/'runtime_summary.json'),
 runtime_verified_frames=[],ice_ram_vram_verified_frames=ram,ice_full_framebuffer_verified_frames=[],ice_user_playtest_accepted=True,
 ice_art_review_pending=False,bank1_set=rel(D/'recipe.json'),current_build_save=CS,agent_loaded_save_state=False,save_roundtrip=None,
 riko_reference_count=201,original_saber_effect_references_preserved=75,preserved_unedited_body_references=[],
 all_current_frames_preview=rel(M/'riko_master_preview_2x.png'),session_state_at_last_observation='Fresh card boot; current banks validated; user accepted ice; F1 saved in pause menu',
 session_state_evidence='work/ver_buki_riko/save_validation/20261025T112700211560Z/progress.local.json',next_task='Ryuenjin animations101/102; preserve accepted ice/spin bodies',
 report='docs/RIKO_HYOURETSUZAN.md')
cur.pop('pending_build',None);write(p,cur)
p=ROOT/'projects/ver_buki_riko/master_sheet.json';cur=read(p);cur.update(source_build=rel(B),source_bin_sha256=H,directory=rel(M),master=rel(M/'master.local.json'),sheet=rel(M/'riko_master_indexed.png'),preview=rel(M/'riko_master_preview_2x.png'),roundtrip=rel(split/'validation.local.json'),riko_references=201,next_group='ryuenjin',report='docs/RIKO_HYOURETSUZAN.md',ice_art_review_pending=False);write(p,cur)
p=ROOT/'docs/RIKO_HYOURETSUZAN.md';s=p.read_text('utf8');s=s[:s.index('## 실행 검증 상태')]+f'''## 실행 검증과 사용자 확인

새 BIN을 부팅하고 CONTINUE→카드 DATA1→Jungle 진입을 직접 관찰했다. 새 bank0/bank1 전체 로딩을 확인했다. `{R}`에서16몸 모두 RAM·VRAM·팔레트가 일치했다. 자동 검사에서 전체 불투명 픽셀 화면 일치는0/16이며, 이것을 통과로 바꾸지 않는다. 실제 캡처에는 물보라·얼음 검 등이 몸과 겹친다. 정확한 각 픽셀 불일치 원인은 모두 확정하지 않았다.

이후 사용자가 “{quote}”라고 직접 실행 성공을 확인하고 다음 작업을 요청했다. **사용자 실행 확인에 따라 현재 빙열참을 채택하며 추가 반복은 중단한다.** 이는 자동 화면16/16 통과나 모든 지형 검사가 아니다. 다음은 용염인101/102다.

현재 세션 `{S}`, 작업용 F1 `{CS}`, 상태 SHA-256 `{save['state_sha256']}`. F1 내부의 현재 bank0 전체·bank1 전체를 검증했다. 제로·8보스0xFF·HP48·Jungle484.1875/426, 메뉴 저장 상태다. 이번 빌드의F3 재시험은 하지 않았다. 기존 F1은 `before_new_f1/`에 보존했다. 카드 해시는 `b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9`로 유지됐다.

Windows 전면 전환 문제는 WScript.Shell의 정상 AppActivate 후 대상 창 포커스 확인으로 해결됐다. 강제 종료·포커스 검사 생략·게임 메모리 쓰기는 하지 않았다. 원본·기존 저장은 보존했다. 추가 공유88/96/99가 나오는 다른 기술 전체와 반대 방향·모든 취소/피격/지형 조합은 미완료다.
''';p.write_text(s,'utf8')
(ROOT/'docs/STATUS.md').write_text(f'''# 프로젝트 상태

2026-10-25 KST. **ZERO_PRODUCTION — 회전 베기 v4와 빙열참 수용, 다음 용염인 제작 진행.** 활성 `ver_buki_riko/zero_riko`, PS1 미국판.

현재 CUE `{rel(B/'riko_motion.cue')}`, BIN SHA-256 `{H}`. 사용자가 직접 빙열참을 실행하고 “{quote}”라고 확인했다. 이에 추가 빙열참 반복은 멈추고 용염인101/102로 진행한다. [빙열참 결과](RIKO_HYOURETSUZAN.md).

누적201몸/섬광과75원본 효과 참조. 회전 베기10몸 PNG를 포함한 기존254 PNG 보존, 기존 원본133과 새 몸/공유 섬광을 Riko로 교체했다.105검사·반복 BIN 동일·74섹터 EDC/ECC·201 PNG/ARC 왕복 통과. 새 부팅과8보스 카드 로드, 현재 bank0/bank1 전체, 빙열참16몸 RAM/VRAM/팔레트 일치. 자동 전체 화면 일치는0/16으로 미확인이며 사용자 실행 관찰과 구분한다. 원본 효과·시간표·판정·EXE·배치는 유지했다.

마스터 `{rel(M)}`. 실행 세션 `{S}`. 작업용 F1 `{CS}`, 상태 SHA-256 `{save['state_sha256']}`. 메뉴 저장, 현재 두 그래픽 은행 확인. 이번 F3 재시험은 미실행이다. 기존 저장·원본 카드 보존.

## 다음 작업과 범위

용염인101/102의11몸 중86/87/160은 현재 아트와 공유한다.144/146/148/150/152/154/156/158을 제작하며 기존 체격·도트·손잡이 기준을 유지한다. 원본 효과123/124와 별도 불꽃의 실제 연결은 확인할 항목이다. 새 기술은 아직 제작·실기 완료가 아니다.

원본 미국판 `SLUS_005.61`,592217136 bytes,SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 설정화 SHA-256 `0537f596cf21b97916b1b59197890fc15a4460fd36026f560b817da471258796`. Buki/Rin/Nana·아머로 확대하지 않는다. 남은 다른 특수 기술·사다리/벽 일부 전체 화면·기절/사망·모든 지형/피격/취소 조합은 미완료다.

[회전 베기](RIKO_AIR_SPIN.md), [용량 정리·복원](STORAGE_MAINTENANCE.md), [명령](COMMANDS.md). 이전 상태·포인터는 `{rel(backup)}`에 보존했다.
''','utf8')
def prepend(name,text):
 p=ROOT/'docs'/name;s=p.read_text('utf8');a,b=s.split('\n',1);p.write_text(a+'\n\n'+text+'\n'+b.lstrip('\n'),'utf8')
prepend('DECISIONS.md',f'## 2026-10-25 — 빙열참 사용자 실행 확인과 용염인 진행\n\n사용자: “{quote}”. 빙열참 현 빌드를 채택하고 자동 전체 화면 대조를 추가 반복하지 않는다. 확인된16몸 RAM/VRAM/팔레트 일치와 사용자 관찰을 구분해 기록한다. 기존 미국판·Riko·같은 길이 그래픽 범위에서 용염인101/102의 미제작8몸과 원본 효과 연결로 진행한다. [근거](RIKO_HYOURETSUZAN.md).\n')
prepend('TEST_RESULTS.md','## 2026-10-25 — 빙열참 새 부팅·메모리 대조·사용자 확인\n\n새 BIN/card 부팅과 두 은행 전체 로딩 확인.16몸 RAM/VRAM/팔레트 일치, 자동 전체 화면0/16. 사용자가 직접 정상 실행을 확인하고 다음 작업을 요청해 반복을 중단했다. F1의 현재 은행 검증·이전 F1 백업·카드 해시 유지 확인. F3 재시험은 미실행. [상세 증거](RIKO_HYOURETSUZAN.md).\n')
print(json.dumps(summary,ensure_ascii=False))
