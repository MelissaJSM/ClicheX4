"""직접 열람·재현검사를 마친 승리 네 자세/선택18 누적 후보를 동결한다."""
from pathlib import Path
import json
from native_pose_pack import write,sha,need,SOURCE_SHA
H=Path(__file__).resolve().parent;out=H/'prepared_victory_ladder01'
proof=json.loads((out/'repro_and_rejections.json').read_text('utf8'));need(proof['passed'],'Verification failed')
need(sha((out/'PL00_U.ARC').read_bytes())==proof['reproduced_arc_sha256'],'Output changed');need(sha((out/'ST0E_U1.ARC').read_bytes())==proof['reproduced_ui_sha256'],'UI changed')
views=['base_comparison.png','fourth_comparison.png','selection18_comparison.png']+[f'partial_{n}.png'for n in range(204,208)]
scripts=['register_victory.py','register_victory_parts.py','prepare_victory_complete.py','sync_victory_selection.py','verify_victory_complete.py','native_pose_pack.py','pack_lowhp_return.py']
record=dict(frozen=True,baseline_bin_sha256=SOURCE_SHA,scope='새 기본/포스 승리204..207 및 선택18. 이전 사다리14·벽12·저체력6·귀환3·선택19..21 누적',replaces_proposal='prepared_ladder_wall_front02/proposal.json',files={n:sha((out/n).read_bytes())for n in('PL00_U.ARC','ST0E_U1.ARC','proposal.json')},source_art={f'victory_inputs01/generated_page{n:02}.png':sha((H/f'victory_inputs01/generated_page{n:02}.png').read_bytes())for n in(1,2)},native_art_manifest='victory_parts01/art_manifest.json',native_art_manifest_sha256=sha((H/'victory_parts01/art_manifest.json').read_bytes()),producer_sources={n:sha((H/n).read_bytes())for n in scripts},actual_readback_visually_reviewed=views,old_coarse_head_body_overwrite=False,wholebody_or_arm_resize=False,source_scale='원화627px 정사각 셀을64native로 고정 변환. 캐릭터별bbox 확대/축소 없음.',edge_material_counts={'204':9,'205':10,'206':4,'207':2},selection18_game207_transform={'x':'x','y':'y-1'},other_selection_frames_exact=24,visual_notes=['네 자세의 머리 갈래·귀 내부·칼라·소매·허리 장식 표현을 같은 대기 기준으로 재작화했다.','포스의 큰 흰 기본소매가 검정/보라/금색 의상으로 바뀌며 부분 아머 조합에서도 팔/몸통/다리 경계가 연결된다.','주먹 높이·접지·원점을 유지했으며 선택18은 새로운 게임207의 정확한 사본이다.'],verification='repro_and_rejections.json',sequence_review='sequences.json',actual_game_or_mips_test=False,independent_reviewer_pending=True,full_art_unification_complete=False,remaining=['기본/포스 남은 등장·공중·대시·특수·차량 등 대기 밀도 재검토/교정','Ultimate 이동 외 공중·대시·벽·피격·사다리·귀환·특수·차량 미술 통일'])
write(out/'FROZEN.json',record)
d=json.loads((H/'findings.json').read_text('utf8'));d['victory_frozen_checkpoint']=record
for r in d['next_priorities']:
 if r['group']=='base_fourth_victory':r.update(status='prepared_frozen_root_art_accepted_runtime_pending',prepared_proposal='prepared_victory_ladder01/proposal.json')
for r in d['key_findings']:
 if r['id']=='STYLE-FOURTH-CLOTH':r['resolved_refs']=sorted(set(r['resolved_refs'])|set(range(204,208)));r['remaining_refs']=[];r['status']='listed_refs_prepared_frozen_not_all_fourth_art_completed'
write(H/'findings.json',d)
with (H/'REPORT.md').open('a',encoding='utf8')as f:f.write('\n## 승리4참조·선택18 누적 동결\n\n`prepared_victory_ladder01/proposal.json`은 사다리 누적본을 대체한다. PL00 `02f092d7…`, ST0E `5afaa587…`. 새204~207 양폼은 대기 기준 머리·칼라·소매·의상 주름으로 재작화했고 이전 몸/머리를 덮어쓰지 않았다. 20인덱스레이어·128부분조합·82GPU파트·1120이전수정조합·508원시참조·448비대상합성·1767비대상조립 보존, 재현 및11잘못된입력 거부 통과. 실제 재추출 기본/포스2장·부분4장·선택1장을 직접 확인했다.\n\n선택18만 game207의 `x,y−1` 사본으로 변경하며 다른24개의 표시·원점·조립 레코드는 동일하다. 큰 초상화90112바이트 및 다른UI는 보존한다. 실제EXE animation39의6스텝과 검토용 WEBP를 남겼다. event128·말단 유지·귀환전환·게임플레이를 실행한 것은 아니며, 실제 MIPS/실기 검사는 루트 담당이다. 전체 미술 통일화는 계속 진행 중이다.\n')
print(sha((out/'FROZEN.json').read_bytes()))
