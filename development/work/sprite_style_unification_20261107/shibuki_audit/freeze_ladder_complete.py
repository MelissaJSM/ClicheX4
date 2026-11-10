"""실제 재추출 열람과 재현 검사를 마친 사다리 묶음만 동결 기록한다."""
from pathlib import Path
import json
from native_pose_pack import write,sha,need,SOURCE_SHA
H=Path(__file__).resolve().parent;out=H/'prepared_ladder_wall_front02'
proof=json.loads((out/'repro_and_rejections.json').read_text('utf8'));need(proof['passed'],'Verification failed')
need(sha((out/'PL00_U.ARC').read_bytes())==proof['reproduced_sha256'],'Output changed')
views=[f'{form}_comparison{k:02}.png'for form in('base','fourth')for k in range(3)]+[f'partial_{n:03}.png'for n in(*range(143,156),183)]
art=[H/'ladder_detail_inputs01'/f'generated_page{k:02}.png'for k in(1,2,3)]+[H/'ladder_detail_inputs01/generated_sleeve143.png',H/'ladder_contact_inputs01/generated.png',H/'ladder_shot_inputs01/generated.png']
scripts=['register_ladder_detail.py','probe_ladder_detail_preservation.py','register_ladder_sleeve143.py','register_ladder_contacts.py','register_ladder_parts.py','register_ladder_shots.py','prepare_ladder_complete.py','verify_ladder_complete.py','native_pose_pack.py','pack_lowhp_return.py']
write(out/'FROZEN.json',{'frozen':True,'baseline_bin_sha256':SOURCE_SHA,'scope':'새 기본/포스 사다리143..155·183, 이전 벽55..66·저체력120..125·정면156..158·선택19..21 누적','replaces_proposal':'prepared_wall_front01/proposal.json','files':{n:sha((out/n).read_bytes())for n in('PL00_U.ARC','ST0E_U1.ARC','proposal.json')},'actual_readback_visually_reviewed':views,'source_art':{p.relative_to(H).as_posix():sha(p.read_bytes())for p in art},'producer_sources':{n:sha((H/n).read_bytes())for n in scripts},'new_heads_and_outfits_and_short_firing_arms':True,'old_coarse_head_body_or_sleeve_overwrite':False,'whole_body_or_arm_resizing':False,'native_mirror_aliases':{'145':[144,-1],'147':[146,0],'148':[149,0],'152':[151,0]},'mirror_method':'동일정방향 타일 공유 후16px 파츠기준 X좌표와반전비트 복원. 그림색·실루엣 무손실, tile16빈슬롯 유지.','body_edge_registration':'새 기본/포스 외곽 차이만 부위별 기존 포스 재질로 등록. 옛 몸체 복원 아님.','contact_registration':'생성된 손·손목 덩어리1px 정수이동 및 생성된 포스짧은부츠만 국소등록. 새머리·몸·꼬리는 접점마스크밖 완전보존.','visual_notes':['후면 큰 단색 머리면 대신 생성원화의 실제 중간톤 머리갈래를 보존했다.','포스 후면/사격에 남던 기본형 흰소매·붉은허리 대신 검정·보라·금색 의상으로 구분한다.','154의 눈(-8,1)과 원점 bbox는 기존과 같고,183은 원래 낮은 후면 위치를 유지한다.','사격150/155의10×8 원배럴과 모든 부분아머 위치·RGBA가 같다.'],'verification':'repro_and_rejections.json','sequence_review':'sequences.json','emulator_or_actual_mips_test':False,'independent_reviewer_test':False,'not_full_style_completion':True,'remaining_groups':['기본/포스 승리 및 남은 앞면 등장','Ultimate 공중·대시·벽·피격·사다리·귀환·특수·차량 등 이동 외 동작']})
text='''

## 사다리14참조 누적 준비본 동결

`prepared_ladder_wall_front02/proposal.json`에 기본/포스143..155·183을 누적했다. 자세한 원화·정합 기록은 `LADDER_PROGRESS.md`에 있다. 새로운8몸체·4반전·2발사팔을 사용하며 이전 벽·저체력·정면·선택화면은 그대로 포함한다. 이 제안은 `prepared_wall_front01`을 대체하므로 둘을 중복 적용하지 않는다.

PL00 SHA `76f19a188ad58dd447eec058b669f8d62a4b8c00f957de3b229aeaa67f37495b`, 선택ST0E SHA `80da6cbfa706a3fce1f79133390ed12b719940046e7670eebda81977d1e2325b`. 단순패킹이 초과한40타일을 해결하려고 그림을 줄이지 않았다. 정확한 좌우반전4쌍을 정방향 타일로 공유하고 조립 반전비트를 복원하여 가장 큰 묶음이30타일이다. 경계tile16은 비워 두었다.

재추출70인덱스레이어·448부분마스크/양팔·257GPU파츠·64원총구·672이전동결조합·508raw·428비대상합성·1717비대상조립 보존이 통과했다. 같은 바이트 재현 및 잘못된입력10건 거부도 통과했다. 기본/포스비교6장과14개부분시트를 모두 실제열람했고, 새후면 머리 명암·의상·짧은사격팔과 부위 연결을 확인했다. 실제EXE38스텝 검증과 검토용WEBP는 게임 플레이나 사다리 물리 실행이 아니다.

`FROZEN.json` 이후 이 후보는 변경하지 않는다. 원본·설정화·활성BIN·포인터·사용자저장·게임은 이 에이전트가 변경하지 않았다. 독립 담당자의 MIPS/실기 결과는 아직 본 동결 증거에 포함하지 않으며, 남은 전체 미술통일화도 완료로 표시하지 않는다.
'''
report=H/'REPORT.md';current=report.read_text('utf8')
if '## 사다리14참조 누적 준비본 동결'not in current:report.write_text(current+text,'utf8')
print(sha((out/'FROZEN.json').read_bytes()))
