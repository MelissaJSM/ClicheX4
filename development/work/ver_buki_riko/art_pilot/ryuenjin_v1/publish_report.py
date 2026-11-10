from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
raise RuntimeError('User rejected this front-facing uppercut. Keep this draft unpublished; use ryuenjin_v2.')
def read(p):return json.loads(p.read_text('utf8'))
def write(p,r):p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
def rel(p):return Path(p).relative_to(ROOT).as_posix()
B=Path(read(D/'builds.json')['build']['output']);H=read(B/'manifest.json')['modified_bin']['sha256']
M=Path(read(D/'master_export.json')['output']);split=Path(read(D/'master_split.json')['output'])
S='work/ver_buki_riko/emulator_sessions/20261025T113913202824Z';R=Path(sys.argv[1]).resolve();v=read(R)
CS=Path(read(D/'checkpoint_preparation.json')['output']);save=read(CS/'manifest.local.json')
ram=[int(n) for n,r in v['frames'].items() if any(s['ram_equal'] and s['vram_equal'] and s['palette_equal'] for s in r['samples'])]
full=v['verified_frames'];pipeline=v['pipeline_verified_frames'];unverified=sorted(set(map(int,v['frames']))-set(full)-set(pipeline))
assert len(ram)==11 and save['bin_sha256']==H and save['full_current_bank1_present']
sectors=len(read(D/'verify_result.json')['changed_sectors'])
summary={'build':rel(B),'bin_sha256':H,'session':S,'evidence':rel(R),'ram_vram_palette_frames':ram,'full_screen_frames':full,
 'separate_sample_full_screen_frames':pipeline,'full_screen_unverified':unverified,'user_art_review_pending':True,
 'current_save':rel(CS),'save_bank0_equal':True,'save_bank1_present':True,'fresh_card_boot_observed':True,'f3_tested_this_build':False,
 'next_group':'remaining special techniques after current art review','process_memory_written':False}
write(D/'runtime_summary.json',summary)
backup=D/'publication_backup';backup.mkdir(exist_ok=False)
for p in [ROOT/'projects/ver_buki_riko/current_build.json',ROOT/'projects/ver_buki_riko/master_sheet.json',ROOT/'docs/STATUS.md']:shutil.copyfile(p,backup/p.name)
p=ROOT/'projects/ver_buki_riko/current_build.json';cur=read(p)
cur.update(kind='riko_wall_spin_ice_rise_bank1_v1',previous_build=cur['build'],previous_bin_sha256=cur['bin_sha256'],previous_pointer_snapshot=rel(backup/'current_build.json'),
 build=rel(B),cue=rel(B/'riko_motion.cue'),bin_sha256=H,session=S,session_closed=False,runtime_summary=rel(D/'runtime_summary.json'),
 runtime_verified_frames=full,rise_ram_vram_verified_frames=ram,rise_full_framebuffer_verified_frames=full,rise_pipeline_verified_frames=pipeline,
 rise_art_review_pending=True,bank1_set=rel(D/'recipe.json'),current_build_save=rel(CS),agent_loaded_save_state=False,save_roundtrip=None,
 riko_reference_count=209,original_saber_effect_references_preserved=83,all_current_frames_preview=rel(M/'riko_master_preview_2x.png'),
 session_state_at_last_observation='Fresh card boot; current banks validated; rising saber tested; F1 saved in pause menu',
 session_state_evidence=rel(CS/'manifest.local.json'),next_task='Remaining special techniques; current Ryuenjin appearance awaits user review',report='docs/RIKO_RYUENJIN.md')
cur.pop('pending_build',None);write(p,cur)
p=ROOT/'projects/ver_buki_riko/master_sheet.json';cur=read(p);cur.update(source_build=rel(B),source_bin_sha256=H,directory=rel(M),master=rel(M/'master.local.json'),sheet=rel(M/'riko_master_indexed.png'),preview=rel(M/'riko_master_preview_2x.png'),roundtrip=rel(split/'validation.local.json'),riko_references=209,next_group='remaining_specials',report='docs/RIKO_RYUENJIN.md',rise_art_review_pending=True);write(p,cur)
(ROOT/'docs/RIKO_RYUENJIN.md').write_text(f'''# Riko 용염인

2026-10-25. PS1 미국판 `SLUS_005.61`, `ver_buki_riko/zero_riko`, ZERO_PRODUCTION.

## 제작과 보존

사용자의 빙열참 실행 확인과 다음 작업 지시에 따라 용염인101/102를 제작했다.11몸 중86/87/160은 기존 빙열참·회전 베기 그림을 공유하며 그대로 보존했다. 새 몸8참조는144/146/148/150/152/154/156/158이다.144는 기존 빙열참 착지,146은 기존 웅크리기33,156/158은 기존 공중24/27을 재사용했다.148..154는 기존 Riko 공중 베기를 참고한 상승 자세다. 원본 제로와 파츠 범위는 로컬에서 비교했고 내장 이미지 도구에는 Riko 파생 그림만 입력했다.

상승 그림의 머리23×19는 기존 기준 그대로, 몸639픽셀은 기존 점프586 대비 약1.09배다. 하나의 배율0.038로 맞춘30×61 자세로, 좁은 원본32×64 파츠 안에 들어간다. 머리·몸·망토를 연결하고 망토 바깥쪽만 작은 위상 변화를 줬다. 바깥으로 벗어난 픽셀0, 각 몸은 연결 요소1개다. 이 수치는 미술 품질의 자동 증명이 아니다. 사용자 미술 검토는 아직 없다.

손에는 짧은 손잡이를 두고 긴 칼날을 그리지 않았다. 원본 효과123/124의145/147/149/151/153/155/157/159와 별도 불꽃 리소스·파츠·팔레트·시간표·판정·EXE·주소를 보존했다.156/158은 팔을 내리는 공중 복귀 자세로, 잔여 효과와의 연결은 실제 검토 대상이다.

- CUE: `{rel(B/'riko_motion.cue')}`
- BIN SHA-256: `{H}`
- 원본 BIN: `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`
- 아트·프롬프트·제작/감사 스크립트: `{rel(D)}`
- 공통 마스터: `{rel(M)}`

105개 자동 검사 통과. 반복 빌드 BIN 동일, 변경{sectors}섹터 EDC/ECC 정상, 원본72참조 무변경 왕복 바이트 동일. 기존276 PNG 전부 동일하며 조립 결과가 달라진 것은 위 새8몸뿐이다. 누적209몸/섬광·83원본 효과,209 PNG와 ARC 마스터 왕복 동일. 최소 압축 여유26바이트. 근거는 `preservation_audit.json`, `packing_checks.json`, `verify_result.json`, `master_split.json`이다.

## 실행 검사

새 BIN 부팅→CONTINUE→카드 DATA1→Jungle 진입을 관찰하고 현재 bank0/bank1을 검증했다. **지상 위+특수D** 일반 입력으로 용염인101/102를 발동했다. 로컬 `work/research/decomp/src/main/player_special.c:1424`의 해금 비트8·위+특수 입력과 실제 실행이 대응했다. 코드의 플랫폼 조건부 부분을 PS1 실행 증거로 대신하지 않았다.

`{rel(R)}`:11몸 RAM/VRAM/팔레트 일치. 같은 시점 전체 화면 일치 {full}, 다른 시점의 전체 화면 일치 {pipeline}, 전체 화면 미확인 {unverified}. 반대 방향·모든 지형/취소/피격·별도 불꽃 전체 픽셀 대조는 하지 않았다. 한 번의 일반 입력 계획으로 기본 발동·상승·하강·복귀를 확인하며 추가 반복으로 진행을 지연하지 않는다. 미술 수용은 사용자 검토 전이다.

현재 세션 `{S}`, 작업용 F1 `{rel(CS)}`, 저장 SHA-256 `{save['state_sha256']}`. 저장 안의 현재 두 그래픽 은행 확인. 이번F3 재시험은 미실행이다. 메뉴 저장이므로 V로 재개한다. 이전 F1과 원본 카드·게임·설정화는 보존했다. 이번 작업에 게임 메모리 쓰기·캐릭터 확대·로직 수정은 없다.
''','utf8')
(ROOT/'docs/STATUS.md').write_text(f'''# 프로젝트 상태

2026-10-25 KST. **ZERO_PRODUCTION — 회전 베기 v4·빙열참 수용, 용염인 새 빌드 실행 검사.** 활성 `ver_buki_riko/zero_riko`, PS1 미국판.

현재 CUE `{rel(B/'riko_motion.cue')}`, BIN SHA-256 `{H}`. 용염인101/102의 새8몸과 기존 공유3몸을 적용했다. 기존276 PNG 전부 보존, 누적209몸/섬광·83효과.105검사·반복 BIN 동일·{sectors}섹터 EDC/ECC·209 PNG/ARC 왕복 통과. [구현과 근거](RIKO_RYUENJIN.md).

새 부팅·8보스 카드 로드·현재 두 그래픽 은행 확인. 용염인11몸 RAM/VRAM/팔레트 일치, 같은 표본 전체 화면 {full}, 다른 표본 전체 화면 {pipeline}, 전체 화면 미확인 {unverified}. 지상 위+D 발동. 사용자 미술 검토·반대 방향·전체 취소/피격/지형 조합은 미완료다.

현재 마스터 `{rel(M)}`, 실행 세션 `{S}`, 작업용 F1 `{rel(CS)}`, 저장 해시 `{save['state_sha256']}`. 메뉴에서 저장했으며 V로 재개할 수 있다. F1의 현재 두 은행은 확인했고 이번 F3 재시험은 하지 않았다. 기존 저장·원본 카드는 보존했다.

## 이전 확정과 다음 작업

사용자가 빙열참을 직접 확인하고 “너무오래걸려서 내가해봤는데 잘되네 다음으로 바로넘어가도될정도야”라고 요청해 추가 반복을 중단했다. 빙열참16몸 로딩과 사용자 확인을 자동 전체 화면0/16과 구분한다. [빙열참](RIKO_HYOURETSUZAN.md), [회전 베기 v4](RIKO_AIR_SPIN.md). 두 기술의 PNG는 이번에도 그대로다.

다음은 남은 특수 기술(뇌신격·낙봉파·질풍아)의 공유 범위를 확인해 제작하는 것이다. 현재 용염인에 대한 사용자 수정 의견이 있으면 반영한다. 다른 특수 기술·사다리/벽 일부 전체 화면·기절/사망·모든 지형/피격/취소 조합과 전체 캐릭터는 미완료다. Buki/Rin/Nana·아머로 확대하지 않았다.

원본 미국판 `SLUS_005.61`,592217136 bytes,SHA-256 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 설정화 SHA-256 `0537f596cf21b97916b1b59197890fc15a4460fd36026f560b817da471258796`. 원본·EXE·판정·시간표·리소스 배치는 보존한다. 이전 상태·포인터 `{rel(backup)}`.
''','utf8')
def prepend(name,text):
 p=ROOT/'docs'/name;s=p.read_text('utf8');a,b=s.split('\n',1);p.write_text(a+'\n\n'+text+'\n'+b.lstrip('\n'),'utf8')
prepend('TEST_RESULTS.md',f'## 2026-10-25 — 용염인\n\n105검사·반복 BIN 동일·{sectors}섹터 EDC/ECC·기존276 PNG 동일·209 PNG/ARC 왕복 동일. 새 부팅 후11몸 RAM/VRAM/팔레트, 전체 화면 같은 표본{full}/다른 표본{pipeline}. 기타 전체 화면{unverified} 및 미술 검토는 미완료. [근거](RIKO_RYUENJIN.md).\n')
prepend('COMMANDS.md',f'''## 2026-10-25 — 빙열참·용염인

실행한 명령이다. 아래 기준점은 해당 PID/빌드 전용이며 재부팅 후에는 새로 검색한다.

```powershell
python work/ver_buki_riko/art_pilot/ryuenjin_v1/finalize.py
python -m unittest discover -s tests -q
python work/ver_buki_riko/art_pilot/ryuenjin_v1/build_and_verify.py
python work/ver_buki_riko/art_pilot/ryuenjin_v1/audit.py
python scripts/capture_jump_cycle.py --build {rel(B)} --baseline {rel(Path(v['baseline']))} --rise --observe
```

동일한 입력 계획을 반복한 빌드 검증과 게임 입력 반복은 구분한다. 빙열참은 사용자 직접 실행 확인에 따라 추가 자동 반복을 멈췄다. [빙열참](RIKO_HYOURETSUZAN.md), [용염인](RIKO_RYUENJIN.md).
''')
p=ROOT/'docs/RIKO_SPECIAL_TECHNIQUES.md';s=p.read_text('utf8');start=s.index('**최신:**');end=s.index('\n\n',start);s=s[:start]+'**최신:** 회전 베기 v4·빙열참은 사용자 수용. 용염인은 새8몸+기존3몸 적용과 한 차례 실행 검사까지 진행했다([용염인](RIKO_RYUENJIN.md)). 미술 검토는 아직 없다. 빙열참 효과121은 실제 parts6이며 잘못된 옛 bank1 효과0/1 추출은 사용하지 않는다.'+s[end:];s=s.replace('몸16과 공유88/96/99 후보 제작. 원래 동작16몸·무기parts6 실기 식별, 새 Riko 후보 실기 대기','몸16과 공유88/96/99 제작.16몸 RAM/VRAM 일치·사용자 직접 실행 수용, 자동 전체 화면 미확인').replace('몸11·효과8 추출. 별도 불꽃 오브젝트 유지·검증 필요','몸11 제작(기존3/신규8), 효과8 보존. 새 부팅·11몸 로딩 확인, 미술 검토 전');p.write_text(s,'utf8')
print(json.dumps(summary,ensure_ascii=False))
