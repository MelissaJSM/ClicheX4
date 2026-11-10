"""Bind final local pointers to tested builds, preserving releases and user saves."""
from pathlib import Path
import hashlib,json,shutil,subprocess
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=ROOT/'out/sprite_style_unification_20261107/final';A=W/'final_application'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not A.exists();A.mkdir()
builds={
 'ver_buki_riko':('sprite_style_unification_20261107_v32','shibuki_riko','677cb525c64e4684ff1daf22d7d52905c9e9f1a0967e015363e038ecc9f60e6d','20261108T051849768024Z'),
 'ver_rin_nana':('sprite_style_unification_20261107_v44','rin_nana','3c05824c27f9d78822aa88d3c1c231768a986ab631d6c1e4ed7c3b725bd2f3c1','20261108T052054377072Z')}
protected=read(W/'protection_before.json')['files'];allowed={f'projects/{p}/current_build.json'for p in builds}
assert read(W/'protection_checkpoint59.json')['passed']
for name,old in protected.items():
 p=ROOT/name;assert {'size':p.stat().st_size,'sha256':sha(p)}==old,name
album=read(D/'SPRITE_INDEX.json');assert album['assembled_count']==4510 and album['partial_layer_count']==2736
after=read(W/'runtime52/ladder_screen_matches.json');before=read(W/'runtime52/before_ladder_screen_matches.json')
assert after['all_new_refs_observed']and before['all_new_refs_observed']
assert read(W/'runtime51/br32_before135_52/screen_matches.json')['before_costume_observed']
proof={}
for project,(folder,stem,expected,session)in builds.items():
 base=ROOT/'out'/project/folder;game=base/(stem+'.bin');cue=base/(stem+'.cue');m=read(base/'manifest.json')
 assert sha(game)==m['modified_bin']['sha256']==expected
 assert all(m[k]for k in('all_disc_sectors_compared','unchanged_sectors_identical','changed_EDC_ECC_valid','disc_readback_verified','gameplay_timing_code_palettes_audio_preserved'))
 native=W/('staging_br_v32_native_checks.json'if project=='ver_buki_riko'else'staging_rn_v44_native_checks.json');assert read(native)['passed']
 pointer=ROOT/'projects'/project/'current_build.json';backup=A/project/'current_build_before.json';backup.parent.mkdir();shutil.copyfile(pointer,backup);old_sha=sha(pointer);r=read(pointer)
 r.update(task='sprite_style_unification',stage='SPRITE_STYLE_UNIFICATION_DELIVERED',build=base.relative_to(ROOT).as_posix(),cue=cue.relative_to(ROOT).as_posix(),sha256=expected,
  status_report='docs/SPRITE_FINAL_HANDOFF_20261108.md',art_review='docs/SPRITE_STYLE_UNIFICATION_20261107.md',previous_pointer=backup.relative_to(ROOT).as_posix(),user_accepted=False,
  implementation_complete=True,confirmed_pending_art_candidates=0,current_session=None,running_bin_sha256=None,
  current_runtime_state='최신 CUE 새 부팅 검증 완료 후 시험 창 종료. 사용자 F1/메모리카드 보존.',
  next_action='최신 CUE를 새로 부팅하고 게임 내 카드로 최종 사용자 플레이 확인. 구체적 결함 제보가 있을 때 해당 동작을 수정.',
  last_test_session=f'work/{project}/emulator_sessions/{session}',sprite_collection='out/sprite_style_unification_20261107/final/ALL_SPRITES_CURRENT.html',
  sprite_png_directory='out/sprite_style_unification_20261107/final/sprites',sprite_album_report='docs/SPRITE_FINAL_HANDOFF_20261108.md',
  sprite_consistency_static_verified=True,representative_sprite_runtime_verified=True,exhaustive_sprite_runtime_verified=False,
  sprite_consistency_runtime_verified=False,sprite_consistency_user_accepted=False,
  sprite_style_final_report='work/sprite_style_unification_20261107/final_application/delivery.json',
  runtime_verification_scope='네 캐릭터 기존 대표 동작 실기 증거 유지. 최종 시부키135 캡슐 전후 및 나나 Ultimate 사다리 전후 최신 자원/실제 화면 추가 확인. 부분 아머 모든 조합·전체 게임·모든 60Hz 프레임 실기는 미완료.')
 write(pointer,r)
 proof[project]={'bin':game.relative_to(ROOT).as_posix(),'cue':cue.relative_to(ROOT).as_posix(),'sha256':expected,'cue_sha256':sha(cue),'manifest':(base/'manifest.json').relative_to(ROOT).as_posix(),'native_checks':native.relative_to(ROOT).as_posix(),'changed_sectors':len(m['modified_bin']['changed_sectors']),'pointer':pointer.relative_to(ROOT).as_posix(),'pointer_before_sha256':old_sha,'pointer_after_sha256':sha(pointer),'backup':backup.relative_to(ROOT).as_posix()}
for name,old in protected.items():
 if name in allowed:continue
 p=ROOT/name;assert {'size':p.stat().st_size,'sha256':sha(p)}==old,name
cards=read(W/'protection_checkpoint59.json')['test_cards']
for source,copy in[
 ('work/ver_rin_nana/overhaul_runtime/preultimate_cards/card2_preultimate.mcr','work/sprite_style_unification_20261107/runtime52/cards/preultimate.mcr'),
 ('work/ver_rin_nana/overhaul_runtime/preultimate_cards/card2_preultimate.mcr','work/ver_buki_riko/sprite_style_checkpoint52/cards/preultimate.mcr'),
 ('work/ver_rin_nana/overhaul_runtime/preultimate_cards/card2_preultimate.mcr','work/ver_rin_nana/sprite_style_checkpoint52/cards/preultimate.mcr'),
 ('work/ver_rin_nana/sprite_style_checkpoint9/cards/rin_allboss.mcr','work/ver_buki_riko/sprite_style_checkpoint52/cards/rin_allboss.mcr')]:cards.append({'source':source,'copy':copy,'sha256':sha(ROOT/source)})
for c in cards:assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
count=subprocess.check_output(['powershell','-NoProfile','-Command','(Get-Process epsxe* -ErrorAction SilentlyContinue | Measure-Object).Count'],text=True);assert count.strip()=='0'
viewed=[f'work/sprite_style_unification_20261107/runtime52/{prefix}actual_ladder_{i:02}.png'for prefix in('','before_')for i in range(1,4)]+['work/sprite_style_unification_20261107/runtime52/actual_top_transitions.png','work/sprite_style_unification_20261107/runtime51/br32_before135_52/capture02_page0.png']
report={'checkpoint':52,'implementation_complete':True,'known_confirmed_art_candidates_remaining':0,'user_accepted':False,'exhaustive_runtime_verified':False,'builds':proof,'protected_unmodified_files':len(protected)-len(allowed),'intentionally_changed_protected_pointers':sorted(allowed),'test_card_pairs_preserved':len(cards),'test_cards':cards,'release_pointer_preserved':True,'original_games_preserved':True,'save_states_preserved':True,'memory_written':False,'F1_F3_sent':False,'epsxe_process_count':0,'assembled_png':4510,'partial_png':2736,'album_sha256':sha(D/'ALL_SPRITES_CURRENT.html'),'sprite_index_sha256':sha(D/'SPRITE_INDEX.json'),'actually_viewed':[{'path':p,'sha256':sha(ROOT/p)}for p in viewed],'runtime':{'nana_before':'work/sprite_style_unification_20261107/runtime52/before_ladder_screen_matches.json','nana_after':'work/sprite_style_unification_20261107/runtime52/ladder_screen_matches.json','shibuki_before':'work/sprite_style_unification_20261107/runtime51/br32_before135_52/screen_matches.json','shibuki_after':'work/sprite_style_unification_20261107/runtime51/br32_arrival135/screen_matches.json'},'report':'docs/SPRITE_FINAL_HANDOFF_20261108.md'}
write(A/'delivery.json',report);write(D/'DELIVERY.json',report)
status='''# 프로젝트 상태

2026-11-08 / **EXPANSION — 네 캐릭터 스프라이트 통일 구현·전달 완료, 최종 사용자 검토 단계.**

활성 작업 ID: `sprite_style_unification`. 리코·시부키·나나·린의 확정된 재작화 목록을 모두 반영했다. 현재 추가 확정 결함과 적용 대기 수정은 없다. 작업량 비율을 완료율로 사용하지 않는다. 모든 게임 진행/부분 아머 조합의 실제 플레이와 사용자 최종 수용은 별도다.

## 현재 결과

- [최종 전달·검증 범위](SPRITE_FINAL_HANDOFF_20261108.md)
- [전체 모음집](../out/sprite_style_unification_20261107/final/ALL_SPRITES_CURRENT.html): 네 캐릭터28폼, 조립4,510표시·변경3,077표시. 실제 BIN 픽셀 대조와 원순서 재생 검사 통과.
- [PNG 모음](../out/sprite_style_unification_20261107/final/sprites/): 조립4,510장 및 부분 아머 층2,736장. 원점·크기·투명도 보존.
- 시부키/리코 [BR32 CUE](../out/ver_buki_riko/sprite_style_unification_20261107_v32/shibuki_riko.cue), BIN SHA-256 `677cb525c64e4684ff1daf22d7d52905c9e9f1a0967e015363e038ecc9f60e6d`.
- 나나/린 [RN44 CUE](../out/ver_rin_nana/sprite_style_unification_20261107_v44/rin_nana.cue), BIN SHA-256 `3c05824c27f9d78822aa88d3c1c231768a986ab631d6c1e4ed7c3b725bd2f3c1`.
- 두 `current_build.json`도 위 최신본으로 갱신했다. 수용 v1.0.0 및 `final_release.json`은 그대로다. [적용·보호 기록](../work/sprite_style_unification_20261107/final_application/delivery.json).

## 마지막 수행 결과

checkpoint51에서 남아 있던 시부키 Ultimate135 두 의상, 나나 Ultimate148/149/150/151/152/153/155 두 의상을 수정·통합했다. checkpoint52에서 시부키135의 캡슐 전후와 나나 사다리 두 의상을 최신 CUE로 실제 확인했다. 꼭대기 전환의 색조와 사격 방향 등 정확한 검증 한계는 전달 문서에 있다. 마지막 실기에서 새 확정 절단·연결부 누락은 발견하지 못했다.

원게임 MIPS·GPU, 모든 디스크 섹터 비교·EDC/ECC·재추출 검사는 통과했다. 마지막 통합에서 EXE·팔레트·오디오·타이밍은 보존했다. 그림이 바뀌지 않은 통과 결과를 반복 검사하거나 이번 신규 검사로 계산하지 않았다. 실제 캡처와 합성 재생은 구별한다.

원본/출시본/사용자 저장자료 등78파일은 그대로이고, 보호 목록 중 의도적으로 갱신한 두 활성 포인터는 이전본을 백업했다. 기존 시험 카드7쌍과 새 사본4쌍도 불변이다. 시험 에뮬레이터는 종료했으며 F1/F3·프로세스 메모리 쓰기는 하지 않았다.

## 확정 조건과 다음 작업

플랫폼은 사용자 선택의 PS1 미국판 `SLUS_005.61`. 원본 BIN SHA-256은 `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`이며 입력 전용이다. 두 버전 제작, 전체 캐릭터/아머 통일, 수정본 적용과 반복 검증은 기존 사용자 지시 범위다. 새 유료 서비스·외부 업로드·원본 수정은 하지 않았다.

최종 사용자 확인을 기다리는 상태이며 다시 진행 허락을 받아야 할 구현 작업은 남아 있지 않다. 최신 CUE 새 부팅 → 게임 내 카드 불러오기로 확인한다. 옛 F3는 이전 자원을 포함할 수 있다. 새 결함이 보고되면 현재 해시와 해당 캐릭터·의상·동작을 기준으로 수정한다.

모든60Hz 프레임/스테이지/부분 아머 조합 실기를 완료했다고 주장하지 않는다. 리코/린 bank1 42..49의 선행 VRAM 의존 참조는 원본을 보존했으며 독립 완성 그림으로 추측하지 않았다.

과거 진행 중·미완료 메모는 [이전 상태 이력](STATUS_HISTORY_BEFORE_SPRITE_HANDOFF_20261108.md)에 보존했다. 현재 상태는 이 문서와 최종 전달 문서를 우선한다. [플랫폼 비교](VERSION_COMPARISON.md), [사용자 결정](DECISIONS.md), [제작 이력](SPRITE_STYLE_UNIFICATION_20261107.md).
'''
(ROOT/'docs/STATUS.md').write_text(status,'utf8')
remaining='''# 스프라이트 통일 작업 — 현재 완료 범위

2026-11-08 / checkpoint52. **확정된 재작화 목록의 구현·적용·최종 모음 정리를 마쳤다.** 현재 추가 확정 재작화 후보와 적용 대기 수정은0개다.

[최종 전달 문서](SPRITE_FINAL_HANDOFF_20261108.md), [전체 모음집](../out/sprite_style_unification_20261107/final/ALL_SPRITES_CURRENT.html), [상태](STATUS.md)를 우선한다. 최신 적용 포인터는 BR32/RN44다. 수용 v1.0.0은 보존했다.

시부키135 및 나나 Ultimate 사다리7참조의 옛 도구 거부/연결 보류는 checkpoint51의 정식 도구 성공과 적용으로 해소됐다. checkpoint52에서 실제 게임 확인까지 추가했다. 현재 차단 요인이 아니다. 자동 승인 거부를 우회한 것이 아니며, 이전 실패를 완료로 바꾼 것도 아니다.

사용자 최종 미술 수용, 모든 스테이지와 부분 아머 전조합 실기는 아직 선언하지 않는다. 구체적인 실기 한계는 최종 전달 문서에 모았다. 새 결함 증거 없이 같은 전체 검사·같은 접근 실패를 반복할 작업 목록으로 확대하지 않는다.

다음은 최신 CUE로 사용자 플레이 확인 후 구체적인 결함이 있을 때 해당 참조를 수정하는 것이다. 이전의 “다음 작업”, “거부”, “전체 미완료” 메모는 [역사 기록](SPRITE_REMAINING_WORK_HISTORY_20261108.md)이며 현재 할 일로 되돌리지 않는다.
'''
(ROOT/'docs/SPRITE_REMAINING_WORK.md').write_text(remaining,'utf8')
print(json.dumps({'builds':{k:v['sha256']for k,v in proof.items()},'protected_unchanged':78,'updated_pointers':2,'test_card_pairs':len(cards),'report_sha256':sha(A/'delivery.json')}))
