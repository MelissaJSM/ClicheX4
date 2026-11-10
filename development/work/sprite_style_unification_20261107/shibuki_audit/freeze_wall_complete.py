"""검사 및 실제 재추출 열람을 완료한 벽 묶음만 동결 기록한다."""
from pathlib import Path
import json
from native_pose_pack import write,sha,need,SOURCE_SHA
H=Path(__file__).resolve().parent;out=H/'prepared_wall_front01'
proof=json.loads((out/'repro_and_rejections.json').read_text('utf8'));need(proof['passed'],'Verification failed')
views=[f'{name}_comparison{k:02}.png'for name in('base','fourth')for k in(0,1)]+[f'partial_{n:03}.png'for n in range(55,67)]
art=[H/'wall_detail_inputs01'/f'generated_page{k:02}.png'for k in(1,2)]+[H/p/'generated.png'for p in('wall_contact_edit01','wall_head_edit01','wall_head_edit02')]+[H/'wall_shot_edits01'/f'generated_page{k:02}.png'for k in(1,2)]
write(out/'FROZEN.json',{'frozen':True,'baseline_bin_sha256':SOURCE_SHA,'scope':'새 기본/포스 벽55..66, 이전 저체력120..125·정면156..158·선택19..21 누적','replaces_proposal':'prepared_front_return01/proposal.json','files':{n:sha((out/n).read_bytes())for n in('PL00_U.ARC','ST0E_U1.ARC','proposal.json')},'actual_readback_visually_reviewed':views,'source_art':{p.relative_to(H).as_posix():sha(p.read_bytes())for p in art},'new_head_and_body_and_firing_arm_art':True,'old_head_body_or_sleeve_overlay':False,'body_stretched':False,'firing_arm_stretched':False,'all_six_original_barrel_rectangles_preserved':True,'uncovered_costume_edge_material_registration':'새 기본/포스 외곽 차이만 기존 팔레트 재질로 맞춤. 과거 몸체 복구·전신 축소가 아님.','visual_notes':['55/57의 과대한 머리·빽빽한 잔선을 23px 주 머리폭과 긴 머리 흐름으로 수정했다.','61/63/65의 새 머리, 벽에 닿는 손 및 발과 새 발사팔의 연결을 16종 부분 조합에서 확인했다.','전체 벽 사격에서 기존 기본 흰 소매가 포스 의상 위로 남는 현상 대신 포스 팔 의상이 적용된다.','머리/팔의 포즈별 명암은 새 원화 해석이며 대기 그림의 모든 픽셀을 복제한 것은 아니다.'],'verification':'repro_and_rejections.json','runtime_verified':False,'native_sequence_simulation':'sequences.json','not_full_style_completion':True,'remaining_groups':['기본/포스 후면 사다리','기본/포스 승리 및 남은 앞면 등장','Ultimate 공중·대시·벽·피격·사다리·귀환·특수·차량 등 이동 외 동작']})
print(sha((out/'FROZEN.json').read_bytes()))
