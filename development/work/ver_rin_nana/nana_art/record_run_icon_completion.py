"""이번 확인 범위를 사실별로 기록한다. 게임 입력과 원본은 변경하지 않는다."""
import json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads((ROOT/p).read_text('utf8'))
def write(p,d):(ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
run='out/ver_rin_nana/nana_run_20261029T062150916963Z'
build='out/ver_rin_nana/nana_run_icon_20261029T063639488649Z'
batch='work/ver_rin_nana/nana_batch_runtime/20261029T063746891761Z/verification.local.json'
icon='work/ver_rin_nana/nana_art/sarangi_menu_v1/live01/verification.json'
summary={'run_source_build':run,'run_source_bin_sha256':read(run+'/manifest.json')['modified_bin']['sha256'],'run_evidence':batch,'ram_vram_verified_frames':[n for n in read(batch)['ram_vram_verified_frames'] if 1<=n<=32],'screen_matched_frames':[n for n in read(batch)['render_matched_frames'] if 1<=n<=32],'screen_unverified_frames':[2,4,12],'all_directions_exhaustively_verified':False,'process_memory_written':False,'new_animation_user_accepted':False}
write(run+'/runtime_summary.local.json',summary)
m=read(run+'/manifest.json');m['runtime_evidence']='runtime_summary.local.json';m['runtime_status']='partial_32_ram_vram_29_screen';m['runtime_verified']=False;write(run+'/manifest.json',m)
summary.update({'applied_build':build,'bin_sha256':read(build+'/manifest.json')['modified_bin']['sha256'],'run_runtime_inherited_via_byte_identical_player_entries':True,'menu_icon_runtime_verified':read(icon)['matched'],'menu_icon_evidence':icon,'menu_icon_opaque_pixels_equal':76,'menu_icon_dim_runtime_verified':False,'PL02_menu_runtime_verified':False,'session':'work/ver_rin_nana/emulator_sessions/20261029T064303523013Z'})
runtime=ROOT/build/'runtime';runtime.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'work/ver_rin_nana/emulator_sessions/20261029T064303523013Z/20261029T064517362875Z.png',runtime/'sarangi_menu_actual.png')
write(build+'/runtime_summary.local.json',summary)
for p in (build+'/manifest.json',build+'/verification.json','projects/ver_rin_nana/current_build.json'):
 d=read(p);d.update({'runtime_verified':False,'runtime_status':'menu_icon_verified_run_partial_inherited','menu_icon_runtime_verified':True,'runtime_evidence':'runtime_summary.local.json','new_animation_user_accepted':False})
 if p.endswith('current_build.json'):d['runtime_evidence']=build+'/runtime_summary.local.json'
 write(p,d)
p='projects/ver_rin_nana/project.json';d=read(p);d['latest_integrated_build']=build;d['active_substage']='NANA_RUN_APPLIED_USER_REVIEW'
d['nana_run']={'build':build,'status':'applied','user_accepted':False,'changed_refs':list(range(1,33)),'runtime_evidence':build+'/runtime_summary.local.json'}
d['nana_weapon_icon']={'build':build,'status':'applied_runtime_verified','name':'사랑이','shape':'나나 전용 권총','menu_only':True,'native_projectiles_and_charge_shots_preserved':True,'runtime_evidence':icon}
write(p,d)
p=ROOT/'docs/STATUS.md';s=p.read_text('utf8');s=s.replace('수용한 대기 도트·팔레트를 고정하여 이동·이동 사격을 제작 중이다.','수용한 대기 도트·팔레트를 유지한 이동·이동 사격32참조와 사랑이 권총 메뉴 아이콘을 추가 적용했다. 이동은32참조 RAM/VRAM·29참조 화면 대조, 권총 메뉴는 실제 표시를 확인했다. 새 이동 미술의 사용자 평가는 대기 중이다.')
s=s.replace('out/ver_rin_nana/nana_idle_shot_20261029T055257544069Z/rin_nana.cue','out/ver_rin_nana/nana_run_icon_20261029T063639488649Z/rin_nana.cue',1).replace('02f8c18047c5705ea247a9f880f7c50a5b1866922a2c68c877a497af6962a3a4','ecc139fdb7e4521bf0f4ad6167f24efc431749881f128378d64f8d203f59f3f2',1)
needle='- 나나 대기·정지 사격10참조/7스트림 적용.'
s=s.replace(needle,'- 이동·이동 사격32참조/16스트림 추가:508압축 참조 비교·독립 ARC 재제작·14변경섹터 EDC/ECC·27단위/4거부 검사 통과. 사랑이 메뉴 아이콘은 PL00/PL02의1타일과2색상행씩 변경,4변경섹터·독립2ARC 재제작·76화면 픽셀 일치. 각 단계 전체251793섹터 비교·보호20파일 유지. [상세와 제한](NANA_PRODUCTION.md).\n'+needle,1)
s=s.replace('나나 대기·정지 사격 이후 모션과 UI·일러스트·개인 효과·음성은 순차 제작 대상이다.','나나 이동·이동 사격 이후 모션과 사랑이 아이콘 이외 UI·일러스트·개인 효과·음성은 순차 제작 대상이다.')
p.write_text(s,'utf8')
p=ROOT/'docs/DECISIONS.md';s=p.read_text('utf8');heading='# 2026-10-29 사랑이 메뉴 아이콘 권총 교체\n\n사용자 “아차차 혹시나하는데 지금 일시정지 메뉴들어왔잖아. 사랑이 저거 총알이아니라 나나 총으로 바꿔줄래? 얘는 그게낫겠다”에 따라 메뉴 무기 아이콘을 나나 전용 권총으로 제작·적용했다. 실제 탄환·차지샷은 기존 보존 정책을 유지한다. 승인된 이동 제작과 같은 적용본에 누적했다. [결과와 실기 제한](NANA_PRODUCTION.md).\n\n';p.write_text(heading+s,'utf8')
p=ROOT/'docs/TEST_RESULTS.md';s=p.read_text('utf8');s=s.replace('# 검사와 실행 증거\n','# 검사와 실행 증거\n\n2026-10-29: [나나 이동·사랑이 메뉴](NANA_PRODUCTION.md), 최신`ecc139fd…`. 이동32참조 RAM/VRAM 일치·29참조 화면 일치, 메뉴76불투명 픽셀 일치. 독립 ARC 재제작·전체섹터 비교·EDC/ECC·보호20파일, 이동 관련27단위·4거부 검사 통과. 화면2,4,12와 PL02/어두운 메뉴의 실기는 미확인. 최신본의 이동 검증은 바이트 동일한 부모 검사 계승이며 사용자 새 이동 미술 수용은 대기 중이다.\n',1)
s=s.replace('아직 미술 수용·BIN 적용·실기 검사는 하지 않았다.','이 문장은 당시 기준안 준비 단계의 기록이다. 이후 미술 승인과 대기·정지 사격 사용자 테스트 수용, 이동 적용으로 진행했으며 현재 상태는 [나나 제작](NANA_PRODUCTION.md)을 따른다.',1);p.write_text(s,'utf8')
p=ROOT/'AGENTS.md';s=p.read_text('utf8').replace('현재 대상은 `ver_rin_nana/x_nana` 기준안이다.','현재 대상은 수용한 기준안을 사용하는 `ver_rin_nana/x_nana` 기본형 제작이다.');p.write_text(s,'utf8')
print(json.dumps(summary,ensure_ascii=False))
