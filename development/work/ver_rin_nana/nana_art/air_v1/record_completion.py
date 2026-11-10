"""공중 적용과 실제 확인 범위를 기록한다. 게임 데이터는 수정하지 않는다."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import digest
def read(p):return json.loads((ROOT/p).read_text('utf8'))
def write(p,d):(ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
build='out/ver_rin_nana/nana_air_20261029T070014731019Z';old='out/ver_rin_nana/nana_run_icon_20261029T063639488649Z';art='work/ver_rin_nana/nana_art/air_v1'
one='work/ver_rin_nana/nana_batch_runtime/20261029T070329729527Z';two='work/ver_rin_nana/nana_batch_runtime/20261029T070707670847Z';cross=read(art+'/crosscheck_runtime.json');a=read(one+'/verification.local.json');b=read(two+'/verification.local.json');frames=set(range(33,55))
ram=frames&set(a['ram_vram_verified_frames']);render=frames&(set(a['render_matched_frames'])|set(b['render_matched_frames'])|set(cross['matched_frames']));assert ram==render==frames
trace=read(one+'/trace.json');positions={str(face):sorted({r[8] for r in trace['rows'] if 33<=r[3]<=48 and r[4]&64==face}) for face in (0,64)};assert all(len(v)==1 for v in positions.values())
summary={'source_build':build,'bin_sha256':read(build+'/manifest.json')['modified_bin']['sha256'],'runtime_verified':True,'scope':'22 air references at least one facing; 52/54 matched in asynchronous framebuffer captures','ram_vram_verified_frames':sorted(ram),'screen_matched_frames':sorted(render),'all_44_direction_combinations_verified':False,'evidence':[one+'/verification.local.json',two+'/verification.local.json',art+'/crosscheck_runtime.json'],'vertical_jump_x_fixed16_by_facing_flag':positions,'process_memory_written':False,'user_art_accepted':False,'session':'work/ver_rin_nana/emulator_sessions/20261029T070056726123Z','save_state_loaded_by_agent':False,'checkpoint':'work/ver_rin_nana/checkpoints/nana_air_verified_20261029T0708','checkpoint_f3_reload_tested':False}
checkpoint=ROOT/summary['checkpoint']/'sstates';summary['checkpoint_files']={p.name:digest(p) for p in checkpoint.iterdir() if p.is_file()}
write(build+'/runtime_summary.local.json',summary)
shutil.copyfile(ROOT/art/'normalized01/family_4x.png',ROOT/build/'art/family_4x.png');shutil.copyfile(ROOT/art/'alignment_checks.json',ROOT/build/'alignment_checks.json')
for p in (build+'/manifest.json',build+'/verification.json','projects/ver_rin_nana/current_build.json'):
 d=read(p);d.update(runtime_verified=True,runtime_scope=summary['scope'],runtime_evidence='runtime_summary.local.json',new_animation_user_accepted=False)
 if p.endswith('current_build.json'):d['runtime_evidence']=build+'/runtime_summary.local.json'
 if p.endswith('manifest.json'):d['verification']['runtime_verified']=True
 write(p,d)
d=read('projects/ver_rin_nana/project.json');d['latest_integrated_build']=build;d['active_substage']='NANA_AIR_APPLIED_USER_REVIEW';d['nana_air']={'build':build,'runtime_evidence':build+'/runtime_summary.local.json','status':'applied_runtime_verified','user_art_accepted':False,'frames':sorted(frames)}
d['nana_run']['continuation_approval']={'quote':'좋아 계속해서 다음작업 진행해','date':'2026-10-29','scope':'직전 적용판에서 다음 공중 제작 진행 승인; 별도 전수 사용자 검사 발언은 없음'}
write('projects/ver_rin_nana/project.json',d)
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');start=s.index('2026-10-29.');end=s.index('\n\n## 현재 적용본',start);s=s[:start]+'2026-10-29. `EXPANSION`, 활성 `ver_rin_nana/x_nana`. 나나 공중22참조를 추가 적용해 기본형 누적64참조다.22참조 모두 RAM/VRAM과 적어도 한 방향의 실제 화면을 확인했다. 공중 미술의 사용자 평가는 대기 중이며 다음 제작은 대시·벽 동작이다. 린·공통 한글/로고·사랑이 권총 아이콘은 계승한다. 풀네임 **아오쿠모 린 / 하나코 나나**. [공중 제작](NANA_AIR.md), [기존 제작](NANA_PRODUCTION.md), [미술 기준](NANA_ART_DIRECTION.md).'+s[end:]
s=s.replace(old+'/rin_nana.cue',build+'/rin_nana.cue',1).replace('ecc139fdb7e4521bf0f4ad6167f24efc431749881f128378d64f8d203f59f3f2',summary['bin_sha256'],1)
s=s.replace('- 이동·이동 사격32참조/16스트림 추가:','- 공중22참조/11스트림 추가:508압축 참조 비교·独立 ARC 재제작·전체251793섹터/11변경섹터 EDC/ECC·보호20파일·27단위/4거부 검사 통과. 눈X와 착지 발Y 정렬, 실제 수직 점프 X 일정.22참조 실제 화면 확인은52/54의 비동기 캡처를 포함하며44방향 조합 전수는 아니다. 새F1 저장, 이전F1·카드 백업 완료. [근거와 한계](NANA_AIR.md).\n- 이동·이동 사격32참조/16스트림 추가:',1).replace('独立','독립')
s=s.replace('나나 이동·이동 사격 이후 모션과 사랑이 아이콘 이외 UI','나나 공중 이후 모션과 사랑이 아이콘 이외 UI');p.write_text(s,'utf8')
p=ROOT/'docs/NANA_PRODUCTION.md';s=p.read_text('utf8');s=s.replace('# 나나 기본형 제작\n','# 나나 기본형 제작\n\n후속: [공중22참조](NANA_AIR.md)를 추가 적용했다. 현재 CUE·검증·다음 범위는 해당 기록과 [STATUS](STATUS.md)를 따른다. 아래는 각 묶음 제작 당시 기록이다.\n',1);s=s.replace('이동·이동 사격의 사용자 미술 평가는 대기 중이다. 다음 제작은 같은 체형·팔레트로 공중 동작과 대시를 이어가는 것이다.','사용자가 “좋아 계속해서 다음작업 진행해”로 후속 진행을 승인하여 [공중 동작](NANA_AIR.md)을 추가했다. 별도 전수 사용자 검사 발언을 만들어 기록하지 않는다.');p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';s=p.read_text('utf8');p.write_text('# 2026-10-29 나나 공중 제작 진행\n\n사용자 “좋아 계속해서 다음작업 진행해”로 직전 사랑이 메뉴/이동 적용판을 기반으로 후속 제작을 진행했다. 승인된 나나 기본형 범위 안에서 점프·낙하·착지와 공중 사격22참조를 추가하며 판정·시간표·실제 탄환·원본 입력은 보존했다. 공중 도트 자체의 사용자 수용은 아직 없다. [적용·실기 기록](NANA_AIR.md).\n\n'+s,'utf8')
p=ROOT/'docs/TEST_RESULTS.md';s=p.read_text('utf8').replace('# 검사와 실행 증거\n','# 검사와 실행 증거\n\n2026-10-29: [나나 공중](NANA_AIR.md), `be23eefe…`.22참조 RAM/VRAM 및 실제 화면 확인(52/54 비동기 캡처 포함,44방향 조합 전수 아님), 수직 점프X 일정. 전체251793섹터/11변경섹터·EDC/ECC·독립 ARC/PNG 재제작·508참조 비교·보호20파일·27단위/4거부 검사 통과. 공중 미술 수용은 사용자 확인 전이다.\n',1);p.write_text(s,'utf8')
p=ROOT/'docs/COMMANDS.md';s=p.read_text('utf8');p.write_text(s+'\n## 2026-10-29 나나 공중 (실행 완료)\n\n원화 정규화→팔 등록→공동 타일 배치→같은 공간 재삽입의 실제 명령은 [NANA_AIR.md](NANA_AIR.md)의 재현 항목에 기록했다. `build_nana_run.py --scope air`는 고정된 사랑이 메뉴 부모 해시와33..54참조만 허용한다.\n','utf8')
print(json.dumps(summary,ensure_ascii=False))
