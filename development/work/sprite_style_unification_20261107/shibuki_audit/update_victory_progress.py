"""누적 사다리 동결과 다음 승리 후보를 기존 전수 장부에 반영한다."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent
p=H/'findings.json';d=json.loads(p.read_text('utf8'))
f=json.loads((H/'prepared_ladder_wall_front02/FROZEN.json').read_text('utf8'))
d['ladder_complete_checkpoint']={**f,'proposal':'prepared_ladder_wall_front02/proposal.json','root_native_mips_gpu_report':'../br_pending_v5_components_native_checks.json','root_visual_review':'기본/포스 재추출6장 및 부분150/183 추가 열람 수용','runtime_verified':False}
for r in d['next_priorities']:
 if r['group']=='base_fourth_rear_ladder':
  r.update(status='prepared_frozen_root_native_verified_runtime_pending',prepared_proposal='prepared_ladder_wall_front02/proposal.json')
 if r['group']=='base_fourth_victory':
  r.update(status='generated_204_205_native_review_206_207_pending',input_manifest='victory_inputs01/manifest.json',candidate='victory_native_page01/registration.json',selection18_exact_transform={'x':'x','y':'y-1'})
for r in d['key_findings']:
 if r['id']=='STYLE-BASE-WALL':r.update(status='prepared_frozen_root_native_verified',resolved_by='prepared_wall_front01 now included in prepared_ladder_wall_front02')
 if r['id']=='STYLE-FOURTH-CLOTH':
  r['resolved_refs']=sorted(set(r['resolved_refs'])|{55,59,63,65});r['remaining_refs']=[204,205,206,207]
 if r['id']=='STYLE-BACK-LADDER':
  r['status']='base_fourth_prepared_frozen_ultimate_still_pending';r['resolved_forms']=['base','fourth'];r['remaining_forms']=['ultimate_before','ultimate_after'];r['resolved_by']='prepared_ladder_wall_front02'
d['victory_working_candidate']={'source':'victory_inputs01/generated_page01.png','source_sha256':'d2a6758546d8a8e3fc68766d5de13aa4185955c487129de2376a96c3b41d0b3b','refs':[204,205],'forms':['base','fourth'],'native':'victory_native_page01/registration.json','not_packed':True,'visually_reviewed':['victory_inputs01/base_current.png','victory_inputs01/fourth_current.png','victory_native_page01/base_comparison.png','victory_native_page01/fourth_comparison.png'],'notes':['수용 대기 대비 부족했던 머릿결·귀 안쪽·칼라·소매/옷단 명암을 새로 그렸다.','고정627셀→64배율, 손 접점과 접지 유지. 두폼 외곽/부분파츠 정합은 후속이다.','206/207 새 그림 및 선택18 동기화는 아직 완료하지 않았다.']}
d['art_review_complete']=False
p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
with (H/'REPORT.md').open('a',encoding='utf8')as o:
 o.write('\n## 승리204~207 후속 준비\n\n사다리14참조 누적 동결본은 루트의 원래 MIPS/GPU 검사도 통과했다. 기존64개 주요 시트 육안 범위와 이후 수정안 검토 범위를 구분해 장부를 갱신했다. 전체 미술 완료는 아니다. 승리204/205의 양폼 첫 새 원화를 고정 축척으로 등록해 대기와 직접 대조했으며 머리 갈래·칼라·소매·옷단 디테일이 개선되었다. 아직 패킹하지 않았다. 206/207·선택18 및 남은 등장과 Ultimate 이동 외 전 동작이 계속 남아 있다.\n\n선택18을 현재 ST0E 자원에서 복원하면 게임207과 `x 그대로, y−1`인 정확한 사본이고 팔레트도 동일하다. 신규207 제작 시 이 변환으로 동기화하며 나머지24개 작은 선택 프레임을 보존할 예정이다. 근거: `victory_inputs01/manifest.json`, `selection18_binding.png`.\n')
print('Updated owned findings and REPORT only.')
