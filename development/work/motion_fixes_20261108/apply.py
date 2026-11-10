from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from common import write,sha
from src.psx_disc import file_hash
builds=json.loads((H/'builds.json').read_text('utf8'));sources=json.loads((H/'sources.json').read_text('utf8'));protection=json.loads((H/'protection_before.json').read_text('utf8'))['files'];allowed=set();changes=[]
for mode,build in builds.items():
 p=ROOT/'projects'/mode/'current_build.json';old=json.loads(p.read_text('utf8'));assert old==sources[mode]['pointer'];assert file_hash(ROOT/Path(build['cue']).with_suffix('.bin'))==build['sha256']
 new={**old,'task':'motion_fixes_20261108','stage':'MOTION_FIXES_APPLIED_REVIEW','build':str(Path(build['cue']).parent).replace('\\','/'),'cue':build['cue'],'sha256':build['sha256'],'status_report':'docs/MOTION_FIXES_20261108.md','previous_pointer':str((H/mode/'current_build_before.json').relative_to(ROOT)).replace('\\','/'),'user_accepted':False,'current_session':None,'running_bin_sha256':None,'current_runtime_state':'수정본 정상 키 실기 확인 후 시험 창 종료. 사용자 원본 카드와 F1/F3는 보존.','runtime_verification_scope':'이번: 나나 기본 점프/대시, 린 좌우 대시, 시부키 기본 대시 사격 실제 RAM/VRAM. 아머 변경은 정적 조립/비교, 블랙 리코 새 배색은 정적 검사. 전체 프레임 실기 완료 아님.','next_action':'새 CUE로 나나 기본형 체격을 우선 사용자 검토. 아머 체감과 블랙 리코 배색 후속 확인.','motion_fixes_report':'docs/MOTION_FIXES_20261108.md','motion_fixes_review':'out/motion_fixes_20261108_review/index.html','sprite_collection_snapshot_precedes_current_motion_fix':True}
 if mode=='ver_buki_riko':new.update(black_zero_policy='shared_bitmap_black_outer_white_inner_riko_palette',black_palette_user_accepted=False,black_palette_runtime_verified=False)
 write(p,new);allowed.add(p.relative_to(ROOT).as_posix())
 project=ROOT/'projects'/mode/'project.json';meta=json.loads(project.read_text('utf8'));write(H/mode/'project_before.json',meta)
 meta.update(active_task='motion_fixes_20261108',stage='EXPANSION',active_substage='MOTION_FIXES_APPLIED_REVIEW',latest_integrated_build=new['build'],latest_integrated_bin_sha256=build['sha256'],current_build_pointer=p.relative_to(ROOT).as_posix(),motion_fixes_report='docs/MOTION_FIXES_20261108.md')
 if mode=='ver_buki_riko':meta['black_zero_policy']=new['black_zero_policy']
 write(project,meta);allowed.add(project.relative_to(ROOT).as_posix());changes.append({'project':mode,'previous_sha256':old['sha256'],'new_sha256':build['sha256'],'cue':build['cue']})
unchanged=[];updated=[]
for n,record in protection.items():
 now=file_hash(ROOT/n)
 if n in allowed:updated.append({'path':n,'before':record['sha256'],'after':now})
 else:assert now==record['sha256'],n;unchanged.append(n)
cards=[]
for mode in builds:
 for name in ('nana_allboss.mcr','rin_allboss.mcr'):
  copy=ROOT/'work'/mode/'motion_fixes_20261108/cards'/name;source=ROOT/'work/ver_rin_nana/sprite_style_checkpoint9/cards'/name
  assert file_hash(copy)==file_hash(source);cards.append(copy.relative_to(ROOT).as_posix())
review=ROOT/'out/motion_fixes_20261108_review/index.html';html=review.read_text('utf8')
for p in sorted(review.parent.glob('*.png')):
 if p.name not in html:html+=f'<article><h2>{p.stem}</h2><img loading="lazy" src="{p.name}"></article>'
review.write_text(html,'utf8')
write(H/'application.json',{'applied':changes,'protected_unchanged':len(unchanged),'protected_count':len(protection),'authorized_pointer_updates':updated,'test_cards_unchanged':cards,'final_v1_0_0_and_final_release_untouched':True,'user_accepted':False})
for name in ('STATUS.md','DECISIONS.md','BLACK_VARIANT_PALETTES.md'):
 shutil.copyfile(ROOT/'docs'/name,H/(name+'.before'))
shutil.copyfile(ROOT/'AGENTS.md',H/'AGENTS.md.before')
status='''# 프로젝트 상태

2026-11-08 / **EXPANSION — 네 캐릭터 동작 제보 수정 적용·대표 동작 실기 확인.**

활성 작업 ID: `motion_fixes_20261108`. 사용자가 실제 관찰한 나나 기본형을 우선 보정하고 포스·얼티밋을 함께 검사했다. 린 대시 머리카락, 시부키 대시 사격 연결, 블랙 리코 검정 외투/흰 안쪽 배색을 두 최신 BIN에 적용했다. 사용자 미술 수용은 아직 확인하지 않았다.

## 현재 결과

- [변경 내용·실기/미확인 범위](MOTION_FIXES_20261108.md), [전후 비교·실제 화면](../out/motion_fixes_20261108_review/index.html).
- 시부키/리코: [최신 CUE](../out/ver_buki_riko/motion_fixes_20261108_v1/shibuki_riko.cue), SHA-256 `7174f95eaf2acef2d371a4de6a12113f1dcea374008fc2ec3d85929126633316`.
- 나나/린: [최신 CUE](../out/ver_rin_nana/motion_fixes_20261108_v1/rin_nana.cue), SHA-256 `52a62c6b00551bd4005eb4febd0f795f9d01652f2345e6df28e98a46f800ffdc`.
- 두 `current_build.json`과 `project.json`의 최신 빌드 정보를 갱신했다. 수용 v1.0.0·`final_release.json`과 원본은 유지했다. [보호/적용 영수증](../work/motion_fixes_20261108/application.json).

## 검사와 한계

두 BIN 각각 전체251,793섹터 비교·EDC/ECC·재추출을 통과했다. X 비대상 레이어4,070개, EXE·게임 타이밍·오디오·타이틀·헌터베이스는 보존했다. 린 대시46/47/48은 다른 머리카락 그림이며 그 밖의 몸 픽셀은 동일하다. 리코는 일반형 팔레트를 보존하고 블랙용 두32바이트 색상표만 교체했다.

새 CUE와 카드 사본을 사용해 나나 기본형 좌우 대시/공중/착지/사격, 린 좌우 대시, 시부키 기본형 좌우 대시 사격의 실제 RAM/VRAM을 확인했다. 실제 화면 일치 표본과 발사 이펙트 가림은 위 보고서에 구분했다. 아머 변경은 정적 조립과 전후 이미지 검사까지이며 모든 부분 아머 실기는 미실행이다. 블랙 리코 새 배색의 실제 커맨드 진입과 저장 화면은 아직 미확인이다. 시험 창은 모두 종료했다.

보호 목록80파일 중76개는 동일하고, 승인된 활성 메타데이터4개만 백업 후 갱신했다. 시험 카드 사본4개도 원래 내용과 동일하다. F1/F3·프로세스 메모리 쓰기는 하지 않았다.

## 입력·승인·다음 작업

PS1 미국판 `SLUS_005.61`. 입력 전용 원본 BIN SHA-256: `3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b`. 이번 네 수정 및 아머 점검은 최신 사용자 요청 범위다. 플랫폼/로직/타이밍 변경, 유료 설치, 외부 공개는 하지 않았다. 작업 차단 요인은 없다.

새 CUE로 부팅하고 게임 내 카드로 불러온다. 옛 F3는 이전 그래픽을 되살릴 수 있다. 다음은 사용자 체감 검토이며, 나나 기본형 점프·하강·착지와 대시 체격을 우선 확인한다. 아머 및 블랙 리코의 미검증 실기 범위를 완료한 것으로 취급하지 않는다.

## 보존한 이전 결과

- [린 헌터베이스 체형·회색 어깨/검은 프릴](RIN_HUNTER_PROPORTIONS_20261108.md): 이번 BIN에 유지. 그 작업의 출격13 실제 화면 일치 포착은 별도 미완료다.
- [스텔라이브 팬 모드 고지·타이틀 부제](TITLE_BRANDING_20261108.md): 이번 BIN에 유지.
- [이전 전체 스프라이트 전달](SPRITE_FINAL_HANDOFF_20261108.md), [전체 모음집](../out/sprite_style_unification_20261107/final/ALL_SPRITES_CURRENT.html): 이번 동작 수정 **이전** 스냅샷. 현재 파일은 위 최신 CUE와 비교 페이지가 우선한다.
- [플랫폼 초기 비교](VERSION_COMPARISON.md), [완성본 보존](FINAL_RELEASE.md), [제작 경험](PRODUCTION_LESSONS.md).
'''
(ROOT/'docs/STATUS.md').write_text(status,'utf8')
dec='''# 2026-11-08 네 캐릭터 동작 수정과 블랙 리코 방향 변경

사용자는 린의 정적인 대시, 나나 점프/대시 체격, 시부키 대시 사격의 팔/버스터 분리, 블랙 리코 무채색 취소를 요청했다. “기본형에서그랬는데 … 다른상태일때도”라는 추가 설명에 따라 나나 기본형을 우선하고 포스/얼티밋에도 같은 좌표 보정을 적용했다. 리코는 검정 외투/흰 안쪽 배색으로 변경하며 일반형과 비트맵 공유를 유지한다. 기존 승인된 그래픽 수정·격리 실행·활성 포인터 갱신 범위다. 새 EXE/타이밍 변경이나 외부 업로드는 없으며 새 디자인의 사용자 수용으로 기록하지 않는다. [결과](MOTION_FIXES_20261108.md).

'''
p=ROOT/'docs/DECISIONS.md';p.write_text(dec+p.read_text('utf8'),'utf8')
p=ROOT/'docs/BLACK_VARIANT_PALETTES.md';p.write_text('''# 최신 변경: 블랙 리코 검정 외투 / 흰 안쪽 의상

2026-11-08 사용자 요청으로 리코 전신 무채색 방향을 폐기했다. 녹색 머리와 피부를 보존하면서 외투와 장화는 검정, 안쪽 의상은 밝은 색으로 바꿨다. 일반/블랙 비트맵 공유, 일반형 팔레트는 유지한다. 공유 하이라이트와 검기 색상 영향, 새 CUE/해시, 정적 검사 및 미실행 실기는 [최신 보고서](MOTION_FIXES_20261108.md)를 따른다. 레드 린의 색상 방향은 그대로다. 아래 무채색 설명과 CUE는 **이전 이력**이다.

'''+p.read_text('utf8'),'utf8')
p=ROOT/'AGENTS.md';s=p.read_text('utf8');s=s.replace('사용자가 지정한 블랙 팔레트 방향은 린의 적색 배색과 리코의 무채색이며, 일반형 색상은 보존한다.','사용자가 지정한 블랙 팔레트 방향은 린의 적색 배색과 리코의 검정 외투/흰 안쪽 의상이며, 일반형 색상은 보존한다. 리코의 이전 전신 무채색 방향은 2026-11-08 사용자 요청으로 폐기했다.');p.write_text(s,'utf8')
print('Applied both builds; protected unchanged',len(unchanged),'pointer files',len(updated),'test cards',len(cards))
